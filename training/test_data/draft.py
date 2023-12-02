import json
import os
from typing import Any, Dict, List
from uuid import UUID

from sqlmodel import Session

from app.groups.models import GroupAccess, Groups
from app.permissions.models import Permissions
from app.roles.models import Roles
from app.users.models import Users
from app.users.serializers import pwd_context
from core.db import SessionContextManager
from manage import ManagementUtility


class FillTestData:
    ROOT_TEST_DATA = "tests/test_data/"
    USERS_FILE = os.path.join(ROOT_TEST_DATA, "users.json")
    PERMISSIONS_FILE = os.path.join(ROOT_TEST_DATA, "permissions.json")
    GROUPS_FILE = os.path.join(ROOT_TEST_DATA, "groups.json")
    ROLES_FILE = os.path.join(ROOT_TEST_DATA, "roles.json")

    def __init__(self):
        with SessionContextManager() as db:
            self.users = self.create_users(db)
            self.roles = self.create_roles(db)
            # should be after roles, due to roles are needed while creating permissions
            self.permissions = self.create_permissions(db)
            self.groups = self.create_groups(db)
            self.create_groups_access(db)
        self.permission_test_data = self.get_permission_test_data()

    @classmethod
    def get_data_from_file(cls, file: str) -> Dict[str, Any]:
        """Reads a JSON file and returns the data as a list of dictionaries.
        Parameters
        ----------
        cls: The class that the method is being called on
        file: str
            Path to file to read from
        Returns
        -------
        [Dict[str, Any]]
        """
        with open(file, "r") as f:
            data = json.loads(f.read())
        return data

    def create_users(self, db: Session) -> List[Dict[str, Any]]:
        """Creates users, and if the user has a group and role, creates GroupAccess.
        Returns
        -------
        List[Dict[str, Any]]
        """
        users = self.get_data_from_file(self.USERS_FILE)["users"]
        for user in users:
            existing_user_id = Users.objects(db).values(Users.id).get_or_none(email=user["email"])
            # if user already created
            if existing_user_id:
                # set user id, group_id and role_id for tests
                user["id"] = str(existing_user_id)
                group_accesses = GroupAccess.objects(db).filter(user_id=existing_user_id)
                user["group_accesses"] = []
                for group_access in group_accesses:
                    user["group_accesses"].append(
                        {"group_id": str(group_access.group_id), "role_id": str(group_access.role_id)})
                continue
            # if user doesn't exist save it
            password = user.get("password")
            # create user with hashed password
            user["password"] = pwd_context.hash(user["password"]) if user.get("password") else ""
            created_user = Users.objects(db).create(**user)
            # set unhashed password again
            user["password"] = password
            user["id"] = created_user.id
            if group_accesses := user.get("groups"):
                user["group_accesses"] = []
                for group_access in group_accesses:
                    group = Groups.objects(db).get_or_none(name=group_access.get("group"))
                    role = Roles.objects(db).get_or_none(name=group_access.get("role"))
                    if not group or not role:
                        continue
                    GroupAccess.objects(db).get_or_create(user_id=created_user.id, group_id=group.id, role_id=role.id)
                    user["group_accesses"].append({"group_id": str(group.id), "role_id": str(role.id)})
            existing_user_id = Users.objects(db).values(Users.id).get_or_none(email=user["email"])
            # if user already created
            if existing_user_id:
                # set user id, group_id and role_id for tests
                user["id"] = str(existing_user_id)
                group_accesses = GroupAccess.objects(db).filter(user_id=existing_user_id)
                user["group_accesses"] = []
                for group_access in group_accesses:
                    user["group_accesses"].append(
                        {"group_id": str(group_access.group_id), "role_id": str(group_access.role_id)})
                continue
            # if user doesn't exist save it
            password = user.get("password")
            # create user with hashed password
            user["password"] = pwd_context.hash(user["password"]) if user.get("password") else ""
            created_user = Users.objects(db).create(**user)
            # set unhashed password again
            user["password"] = password
            user["id"] = created_user.id
            if group_accesses := user.get("groups"):
                user["group_accesses"] = []
                for group_access in group_accesses:
                    group = Groups.objects(db).get_or_none(name=group_access.get("group"))
                    role = Roles.objects(db).get_or_none(name=group_access.get("role"))
                    if not group or not role:
                        continue
                    GroupAccess.objects(db).get_or_create(user_id=created_user.id, group_id=group.id, role_id=role.id)
                    user["group_accesses"].append({"group_id": str(group.id), "role_id": str(role.id)})
            existing_user_id = Users.objects(db).values(Users.id).get_or_none(email=user["email"])
            # if user already created
            if existing_user_id:
                # set user id, group_id and role_id for tests
                user["id"] = str(existing_user_id)
                group_accesses = GroupAccess.objects(db).filter(user_id=existing_user_id)
                user["group_accesses"] = []
                for group_access in group_accesses:
                    user["group_accesses"].append(
                        {"group_id": str(group_access.group_id), "role_id": str(group_access.role_id)})
                continue
            # if user doesn't exist save it
            password = user.get("password")
            # create user with hashed password
            user["password"] = pwd_context.hash(user["password"]) if user.get("password") else ""
            created_user = Users.objects(db).create(**user)
            # set unhashed password again
            user["password"] = password
            user["id"] = created_user.id
            if group_accesses := user.get("groups"):
                user["group_accesses"] = []
                for group_access in group_accesses:
                    group = Groups.objects(db).get_or_none(name=group_access.get("group"))
                    role = Roles.objects(db).get_or_none(name=group_access.get("role"))
                    if not group or not role:
                        continue
                    GroupAccess.objects(db).get_or_create(user_id=created_user.id, group_id=group.id, role_id=role.id)
                    user["group_accesses"].append({"group_id": str(group.id), "role_id": str(role.id)})

        return users

    def create_permissions(self, db: Session) -> List[Dict[str, Any]]:
        """Creates permissions for a role.
        Returns
        -------
        List[Dict[str, Any]]
        """
        permissions = self.get_data_from_file(self.PERMISSIONS_FILE)["permissions"]
        for permission in permissions:
            role = Roles.objects(db).get_or_none(name=permission.get("role"))
            if not role:
                continue
            for action in permission.get("actions"):
                Permissions.objects(db).get_or_create(
                    role_id=role.id,
                    action=action,
                    entity=permission["entity"],
                )
            permission["role_id"] = str(role.id)
        return permissions

    def create_groups(self, db: Session) -> List[Dict[str, Any]]:
        """
        Create groups based on config file
        :return: list of groups
        """
        group_data = self.get_data_from_file(self.GROUPS_FILE)["groups"]
        for group in group_data:
            group_exists = Groups.objects(db).exists(**group)
            if group_exists:
                continue
            group_path, parent_id = ManagementUtility.generate_path_and_parent(db=db)
            group["parent_id"] = parent_id
            query = Groups(**group)
            query.path = group_path
            Groups.objects(db).save_model(query)
        return group_data

    def create_roles(self, db: Session) -> List[Dict[str, Any]]:
        """
        Create roles based on config file
        :return: list of roles
        """
        role_data = self.get_data_from_file(self.ROLES_FILE)["roles"]
        for role in role_data:
            Roles.objects(db).get_or_create(**role)
        return role_data

    @staticmethod
    def _get_action_and_expected_result(actions: list[str]) -> list[list[str, bool]]:
        """
        Prepare actions and expected result for tests
        :param actions: permission actions
        :return: list of lists with action and expected_result
        """
        all_actions = ("read", "update", "create", "delete")
        result = []
        for action in all_actions:
            if action in actions:
                result.append([action, True])
            else:
                result.append([action, False])
        return result

    def get_permission_test_data(self):
        """
        Create test data for checking permissions
        :return: dict[str: dict]
        """
        users_and_permissions_data = list(zip(self.permissions, self.users))
        result = {}
        for permission, user in users_and_permissions_data:
            result[permission["role"]] = {
                "is_entity_user": permission["entity"] == "user",
                "email": user["email"],
                "actions": self._get_action_and_expected_result(permission["actions"])
            }
        return result

    @staticmethod
    def _crt_grp_accss(db: Session, group_id: UUID, user_ids: list[UUID], role_names: tuple):
        """
        Create group access for entity
        P.S. user_roles and group_roles should be in this following,
        don't change it
        :param group_id: group_id
        :param user_ids: user ids for which will be created group_access
        :param role_names: list of entity names
        :return: None
        """

        for index, role_name in enumerate(role_names):
            user_id = user_ids[index]
            role = Roles.objects(db).get_or_none(name=role_name)
            role_id = role.id
            GroupAccess.objects(db).get_or_create(
                defaults={"role_id": role_id},
                user_id=user_id,
                group_id=group_id
            )

    def crtGrp1212acsss(self, db: Session) -> None:
        """
        Create groups access for each entity (user/group)
        :return: None
        """
        user_roles = ("DA Admin", "Manager", "User")
        group_roles = ("Group DA Admin", "Group Manager", "Group User")
        role_roles = ("Role DA Admin",)
        users = Users.objects(db).all()
        user_ids = [user.id for user in users]

        # For USER entity
        first_group_id = Groups.objects(db).get_or_none(name=self.groups[0]["name"]).id
        self._create_group_access_entity(db=db, group_id=first_group_id, user_ids=user_ids[:3], role_names=user_roles)

        # For GROUP entity
        second_group_id = Groups.objects(db).get_or_none(name=self.groups[1]["name"]).id
        self._create_group_access_entity(db=db, group_id=second_group_id, user_ids=user_ids[3:], role_names=group_roles)

        # For Role entity
        self._create_group_access_entity(db=db, group_id=first_group_id, user_ids=user_ids[:1], role_names=role_roles)
