import re
from collections import defaultdict
from typing import Any, Dict, List, NamedTuple, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, not_, or_, select
from sqlalchemy.engine import Row
from sqlalchemy_utils import Ltree
from sqlmodel import Session
from sqlmodel.sql.expression import SelectOfScalar
from treelib import Node

from app.groups.models import GroupAccess, Groups
from app.groups.utils import get_groups_by_user_level
from app.permissions.models import PermissionActionChoose, Permissions
from app.permissions.services import PermissionService
from app.roles.models import RoleLevelChoose, Roles
from app.users.models import Users
from app.users.serializers import CreateUsersResponseSerializer
from constants import ADMIN_GROUP_PATH
from utils.helper_funcs import construct_role_list_response
from utils.ltree_utils import ltree_order_query
from utils.tree import GroupHierarchyTree


class HierarchyPermissionsResponse(NamedTuple):
    """Tuple to return user permissions to access group hierarchy."""

    has_access_to_groups: bool
    has_access_to_users: bool
    level: Optional[str]

    @staticmethod
    def no_permissions():
        """Return no access result (no access to groups, to users and no role level)."""
        return HierarchyPermissionsResponse(False, False, None)

    @staticmethod
    def read_users_and_groups_permissions(level: str):
        """Return full access result (access to groups, to users and defined role level)."""
        return HierarchyPermissionsResponse(True, True, level)

    @staticmethod
    def read_groups_permissions(level: str):
        """Return partial access result (access to groups, but no access to users and defined role level)."""
        return HierarchyPermissionsResponse(True, False, level)


class GroupHierarchyService:
    """Service for creating and getting group hierarchy structure."""

    def __init__(self):
        # initialize empty tree
        self.tree = GroupHierarchyTree()
        self.children_of_current_to_show = {}

    @staticmethod
    def update_node_data(node: Node, node_data: Dict[str, Any]) -> Node:
        """Update the node's data.
        Parameters
        ----------
        node: Node
            The node to update
        node_data: Dict[str, Any]
            A dictionary of data to be added to the node
        Returns
        -------
        Updated node
        """
        node.data.update(node_data)
        return node

    @staticmethod
    def get_group_access_nodes(
        db: Session, user_id: UUID, group_ids_query: Optional[SelectOfScalar] = None
    ) -> List[Row]:
        """Finds all groups user has access to."""
        group_access_query = (
            select(Groups.id, Groups.path, Roles.level)
            .select_from(GroupAccess)
            .join(Groups, Groups.id == GroupAccess.group_id)
            .outerjoin(Roles, Roles.id == GroupAccess.role_id)
            .filter(GroupAccess.user_id == user_id)
        )
        if group_ids_query is not None:
            group_access_query = group_access_query.filter(Groups.id.in_(group_ids_query))

        return db.execute(group_access_query.order_by(ltree_order_query(ordering="asc"))).all()

    def find_or_create_parent_in_tree(self, path: Ltree, node_data: Optional[Dict[str, Any]] = None) -> Node:
        """Finds the node in the tree that corresponds to path or creates it and its parents if they don't exist.
        Parameters
        ----------
        path: Ltree
            The path of the node to be found or created
        node_data: Optional[Dict[str, Any]]
            The data that will be stored in the node
        Returns
        -------
        Found or created node
        """

        # if node has no level, we have no access to it, so it couldn't be nested, set it as current
        # also set name by default to make it possible to sort if node has no name(was deleted)
        default_data = {"level": RoleLevelChoose.current, "name": ""}

        # if we have node in tree, update it with new data
        if node := self.tree.get_node(str(path)):
            return self.update_node_data(node, node_data)

        # if node is root, create it without parent
        if len(path) == 1:
            return self.tree.create_node(str(path), str(path), data=node_data)

        # if user is added to group that has parent with current level, skip hierarchy between
        if path in self.children_of_current_to_show.keys():
            parent_path = self.children_of_current_to_show[path]
        else:
            parent_path = path[:-1]

        # recursively find or create node parent by path
        parent = self.tree.get_node(str(parent_path))
        return self.tree.create_node(
            str(path),
            str(path),
            parent or self.find_or_create_parent_in_tree(parent_path, default_data),
            data=node_data,
        )

    def get_groups_by_tree_level(self, db: Session, group_access_nodes: List[Row]) -> List[Optional[Groups]]:
        """Returns a list of all the groups that are descendants of the nodes in the tree
        Returns
        -------
        A list of groups
        """
        current_groups_path, group_queries, excluded_current_groups_query, show_current_children_query = [], [], [], []
        paths_current_groups = [group.path for group in group_access_nodes if group.level == RoleLevelChoose.current]

        # if user's added to group with (current_)nested level that has parent with current level
        # we should get their children even though they are successors of upper current level group
        paths_current_children = [path for path in self.children_of_current_to_show if path not in paths_current_groups]

        # if node's level is current, use in_() query, else find object and its children
        for node in self.tree.all_nodes_itr():
            node_path = Ltree(node.identifier)
            if node.data["level"] == RoleLevelChoose.current:
                current_groups_path.append(node_path)
            else:
                group_queries.append(Groups.path.descendant_of(node_path))
        group_queries.append(Groups.path.in_(current_groups_path))

        for path in paths_current_children:
            show_current_children_query.append(not_(Groups.path.descendant_of(path)))

        for path in paths_current_groups:
            # for groups with current level, get their info, but do not get their children
            excluded_current_groups_query.append(
                not_(
                    and_(
                        Groups.path.descendant_of(path),
                        Groups.path != path,
                        Groups.path.notin_(self.children_of_current_to_show),
                        *show_current_children_query,
                    )
                ),
            )

        # find all groups using or-statement
        query = select(Groups).filter(or_(*group_queries)).filter(and_(*excluded_current_groups_query))

        return db.execute(query)

    @staticmethod
    def add_users_to_nodes(db: Session, nodes: List[Node]) -> None:
        """Adds users data to hierarchy nodes."""
        node_ids = [node.data["id"] for node in nodes]

        if not node_ids:
            return

        # find users using in_ statement
        users_query = (
            select(Users, Groups.path.label("group_path"), Roles.is_invisible)
            .join(GroupAccess, GroupAccess.user_id == Users.id)
            .join(Groups, Groups.id == GroupAccess.group_id)
            .outerjoin(Roles, Roles.id == GroupAccess.role_id)
            .filter(Groups.id.in_(node_ids))
            .distinct(Users.id, Groups.path)
        )
        groups = defaultdict(list)
        # find node by group path from query and add children to them
        for user, group_path, is_invisible in db.execute(users_query).fetchall():
            if not is_invisible:
                groups[str(group_path)].append(CreateUsersResponseSerializer(**user.dict()))

        for node in nodes:
            node.data["users"] = groups[node.data["path"]]

    def mark_nodes_as_disabled(self, group_access_nodes: List[Row]) -> None:
        """Marks all parental and nested nodes as disabled.
        Parameters
        ----------
        group_access_nodes: List[Row]
            A list of group access rows from db. Each row should contain a path and a level
        """
        parent_paths = [group_access.path for group_access in group_access_nodes]
        nested_paths = [
            group_access.path for group_access in group_access_nodes if group_access.level == RoleLevelChoose.nested
        ]

        # disabled node:
        # a. it's not a child any of nodes from group access query - > so we added it as parent
        # b. node with `nested` level from group access query
        for node in self.tree.all_nodes_itr():
            node_path = Ltree(node.identifier)
            node.data["has_access"] = (
                any(node_path.descendant_of(path) for path in parent_paths) and node_path not in nested_paths
            )

    def get_filtered_data(
        self,
        group_access_nodes: List[Row],
        ordering_fields: List[Optional[str]],
        order_by: Optional[str] = "",
        search_pattern: Optional[str] = None,
        return_without_head: bool = False,
    ) -> List[Dict[str, Any]]:
        """Filters and orders groups hierarchy data.
        Parameters
        ----------
        group_access_nodes: List[Row]
            A list of group access rows from db. Each row should contain a path and a level
        ordering_fields: List[Optional[str]]
            List of possible fields to be ordered by
        order_by: Optional[str]
            The field to order by
        search_pattern: Optional[str]
            The search pattern to filter the tree by
        return_without_head: Optional[bool]
            Whether to remove the head node from the tree, by default False
        Returns
        -------
        A list of filtered dictionaries.
        """
        # validate and setup ordering
        reverse = False
        ordering_field = None

        if order_by:
            reverse = order_by.startswith("-")
            ordering_field = order_by.replace("-", "").replace("+", "")
            if ordering_field not in ordering_fields:
                raise HTTPException(status_code=400, detail="Invalid `order_by` value.")

        # search through the data
        self._search_through_tree_nodes(search_pattern=search_pattern)
        response = self.get_group_tree_as_dict(
            group_access_nodes=group_access_nodes,
            order_by=order_by,
            ordering_field=ordering_field,
            reverse=reverse,
            return_without_head=return_without_head,
        )
        return response

    def get_group_tree_as_dict(
        self,
        group_access_nodes: List[Row],
        order_by: Optional[str] = None,
        ordering_field: Optional[str] = None,
        reverse: Optional[bool] = None,
        return_without_head: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get list with nested dicts instead of Tree object."""

        if order_by and ordering_field:
            tree_dict = self.tree.to_dict(
                with_data=True,
                sort=bool(order_by),
                key=lambda x: x.data[ordering_field],
                reverse=reverse,
            )
        else:
            tree_dict = self.tree.to_dict(with_data=True)

        # if user has access to admin group, return it, otherwise return only children organisations
        return self._make_tree_dict_iterable(
            tree_dict=tree_dict,
            groups_path_list=[group.path for group in group_access_nodes],
            return_without_head=return_without_head,
        )

    @staticmethod
    def _make_tree_dict_iterable(
        tree_dict: Dict[str, Any], groups_path_list: List[Ltree], return_without_head: bool
    ) -> List[Dict[str, Any]]:
        """Makes an iterable of dictionaries from a tree dict for searching and pagination.

        :param tree_dict: The tree dictionary that we want to make iterable
        :param groups_path_list: A list of Ltree objects that represent the groups that the user is a member of
        :param return_without_head: If True, the root node will be removed from the tree
        """

        system_group_path = Ltree(ADMIN_GROUP_PATH)
        # if AdminGroup is head and user has no access to it, remove it
        if tree_dict["path"] == system_group_path and system_group_path not in groups_path_list:
            return tree_dict["children"]
        # if boolean flag to remove head is True, remove it
        if return_without_head:
            return tree_dict["children"]

        return [tree_dict]

    def  _search_through_tree_nodes(self, search_pattern: str) -> None:
        """For each node in the tree, check if the node's name matches the search pattern.

        :param search_pattern: The search pattern to use
        """
        if not search_pattern:
            return
        search_pattern = re.compile(".*".join(search_pattern.lower().split()), re.IGNORECASE)

        for node in self.tree.all_nodes_itr():
            node_name_lower = node.data["name"].lower()
            node.data["matches_search_term"] = bool(search_pattern.match(node_name_lower))

    def _create_tree_from_group_accesses(self, group_access_nodes):
        """Fill tree using groups user has access to."""
        for node in group_access_nodes:
            node_data = dict(node)
            # if user has no role in group, set level as current
            if not node.level:
                node_data["level"] = RoleLevelChoose.current
            self.find_or_create_parent_in_tree(node_data["path"], node_data)

    def build_tree_from_db_completely(self, db: Session, group_access_nodes: List[Row]) -> None:
        """Build parent tree nodes using user group accesses and then fill children nodes.
        :param db: Session
        :param group_access_nodes: a list of rows contains GroupAccess.id, Groups.path, Roles.level
        """
        # create tree from group_accesses
        self._create_tree_from_group_accesses(group_access_nodes)

        # find needed data from db and add it to tree
        for node in self.get_groups_by_tree_level(db, group_access_nodes):
            self.find_or_create_parent_in_tree(node.Groups.path, node.Groups.dict())

    def set_current_children(self, group_access_nodes: List[Row]) -> None:
        """Set nodes that are children of groups with current level."""
        for node in group_access_nodes:
            for parent in group_access_nodes:
                if (
                    parent.path != node.path
                    and node.path.descendant_of(parent.path)
                    and parent.level == RoleLevelChoose.current
                ):
                    self.children_of_current_to_show[node.path] = parent.path

    def get(
        self,
        db: Session,
        user_id: UUID,
        ordering_fields: List[Optional[str]],
        order_by: Optional[str] = "",
        search_pattern: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Creates group hierarchy using data from db for current user.
        Parameters
        ----------
        db: Session
        user_id:UUID
            The user id of the user whose groups we want to get
        ordering_fields: List[Optional[str]]
            List of possible fields to be ordered by
        order_by: Optional[str]
            The field to order by
        search_pattern: Optional[str]
            The search pattern to filter the tree by
        Returns
        -------
        A list of nested filtered dictionaries with group data.
        """
        # get all user group accesses
        group_access_nodes = self.get_group_access_nodes(db, user_id)

        # if no user groups found, return empty list
        if not group_access_nodes:
            return []

        self.set_current_children(group_access_nodes)
        self.build_tree_from_db_completely(db, group_access_nodes)

        # set disabled marks and add users to data
        self.mark_nodes_as_disabled(group_access_nodes)

        nodes = list(filter(lambda x: x.data["has_access"], self.tree.all_nodes()))
        self.add_users_to_nodes(db, nodes)

        # filter and search
        return self.get_filtered_data(group_access_nodes, ordering_fields, order_by, search_pattern)

    def get_hierarchy_for_navigation(self, db: Session, user_id: UUID) -> List[Dict[str, Any]]:
        """Create group hierarchy for navigation (without users and filtering)
        Parameters
        ----------
        db: Session
        user_id:UUID
            The user id of the user whose groups we want to get
        Returns
        -------
        A list of nested filtered dictionaries with group data.
        """
        # get all user group accesses
        group_access_nodes = self.get_group_access_nodes(db, user_id)

        # if no user groups found, return empty list
        if not group_access_nodes:
            return []

        self.set_current_children(group_access_nodes)
        self.build_tree_from_db_completely(db, group_access_nodes)

        # set disabled marks and add users to data
        self.mark_nodes_as_disabled(group_access_nodes)

        # filter and search
        return self.get_group_tree_as_dict(group_access_nodes=group_access_nodes)

    def _build_tree_for_assign_hierarchy_groups(self, groups_user_has_access_to: List[Groups]) -> None:
        """Take a list of groups that the user has access to and build a tree of those groups

        :param groups_user_has_access_to: List[Row] - list of groups that the user has access to
        """
        for group in groups_user_has_access_to:

            node_id = str(group.id)
            parent_node_id = str(group.parent_id)
            group_data = group.dict()
            group_data["users"] = []

            if node_id not in self.tree:
                # if parent in tree, add group to parent
                if parent_node_id in self.tree:
                    self.tree.create_node(node_id, node_id, parent=parent_node_id, data=group_data)
                # otherwise add group to root
                else:
                    self.tree.create_node(node_id, node_id, data=group_data)

    def _find_user_role_permissions_to_get_hierarchy(self, db: Session, user_id: UUID, group: Groups) -> List[Row]:
        """Return a list of rows that contain the user's role permissions for a given group

        :param user_id: UUID - current user id
        :param group: Groups - group to find permissions for
        :return: A list of rows with structure Row[group_id, group_name, role_id, entity, action]
        """
        permission_service = PermissionService(user_id=user_id)
        role_permission_rows = (
            (
                permission_service.get_user_role_permissions_by_group_not_filtered_by_nested(
                    db=db,
                    values=[
                        Groups.id.label("group_id"),
                        Groups.name.label("group_name"),
                        Roles.id.label("role_id"),
                        Permissions.entity.label("entity"),
                        Permissions.action.label("action"),
                        Roles.level,
                    ],
                    group=group,
                )
            )
            .order_query("desc")
            .all()
        )

        return role_permission_rows

    def _check_if_group_permissions_to_read_users_exist(self, db: Session, user_id: UUID, group: Groups) -> bool:
        """Check if the user has permission to read users in the group

        :param user_id: UUID - the user id of the user who is trying to read the users
        :param group: Groups - group in which user should be and want to read other users
        :return: A boolean value that displays if user has access to other users.
        """

        permission_service = PermissionService(user_id=user_id)
        permission_service.get_user_group_permissions_by_actions_and_group(
            db=db, values=[GroupAccess.id], group_id=group.id, actions=["read"], entities=["user"]
        )
        return bool(permission_service.query.first())

    def _find_permissions_for_group_hierarchy_user_has(
        self, db: Session, user_id: UUID, group: Groups
    ) -> Tuple[bool, bool, Optional[str]]:
        """Check if a user has role permissions to a group and its users

        :param user_id: UUID - the user id for which we are checking the permissions
        :type user_id: UUID
        :param group: Groups - the group for which we are looking for permissions
        :type group: Groups
        """
        response = HierarchyPermissionsResponse

        # find user role permissions in the group or groups upper with convenient level
        role_permission_rows = self._find_user_role_permissions_to_get_hierarchy(db=db, user_id=user_id, group=group)

        # if no role permissions found, check if user in group
        if not role_permission_rows:

            # if user in group, check if user has access to read other users in this group
            if GroupAccess.objects(db).exists(group_id=group.id, user_id=user_id):
                has_access_to_users = self._check_if_group_permissions_to_read_users_exist(db, user_id, group)

                return (
                    response.read_users_and_groups_permissions(RoleLevelChoose.current)
                    if has_access_to_users
                    else response.read_groups_permissions(RoleLevelChoose.current)
                )

            # if user not in group
            return response.no_permissions()

        # if there are role permissions: group all of them by action and find first permission with role
        role_permissions_grouped = construct_role_list_response(role_permission_rows)
        role_permission_row = next((row for row in role_permissions_grouped if row.get("role")), None)

        if not role_permission_row:
            return response.no_permissions()

        permissions = role_permission_row["permissions"]
        level = role_permission_row.get("role_level", RoleLevelChoose.current)

        # if role level is nested, set it current_and_nested if group is parental to current
        if level == RoleLevelChoose.nested and role_permission_row.get("id") != group.id:
            level = RoleLevelChoose.current_and_nested

        # check if user has access to read other users in this group
        return (
            response.read_users_and_groups_permissions(level)
            if PermissionActionChoose.read in permissions.get("user", [])
            else response.read_groups_permissions(level)
        )

    def get_assignee_hierarchy(
        self,
        db: Session,
        group_id: UUID,
        user_id: UUID,
        ordering_fields: List[Optional[str]],
        order_by: Optional[str] = "",
        search_pattern: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Creates hierarchy filtered by header and user level with users for every Groups obj.
        Parameters
        ----------
        db: Session
        group_id:UUID
            The group id from header
        user_id:UUID
            The user id of the user whose groups we want to get
        ordering_fields: List[Optional[str]]
            List of possible fields to be ordered by
        order_by: Optional[str]
            The field to order by
        search_pattern: Optional[str]
            The search pattern to filter the tree by
        Returns
        -------
        A list of nested filtered dictionaries with group data.
        """
        group = Groups.objects(db).get_or_404(id=group_id)

        has_access_to_groups, has_access_to_users, level = self._find_permissions_for_group_hierarchy_user_has(
            db=db, user_id=user_id, group=group
        )

        if not has_access_to_groups:
            return []

        return_without_head = False

        # if level is nested, we need to build all tree and then remove the first level
        if level == RoleLevelChoose.nested:
            level = RoleLevelChoose.current_and_nested
            return_without_head = True

        groups_user_has_access_to: List[Row] = (
            db.execute(
                get_groups_by_user_level(db=db, group_id=group_id, level=level, fields=[Groups], should_be_ordered=True)
            )
            .scalars()
            .all()
        )

        # build tree for groups node by node with or without parent
        self._build_tree_for_assign_hierarchy_groups(groups_user_has_access_to)

        if has_access_to_users:
            self.add_users_to_nodes(db, self.tree.all_nodes_itr())

        # filter and search
        return self.get_filtered_data(
            group_access_nodes=groups_user_has_access_to,
            ordering_fields=ordering_fields,
            order_by=order_by,
            search_pattern=search_pattern,
            return_without_head=return_without_head,
        )
