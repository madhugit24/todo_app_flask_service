import requests
import os


class KeycloakConfig:
    """
    Keycloak configuration class
    """

    def __init__(self):
        """
        Initializes the Keycloak configuration
        """
        self.keycloak_url = os.environ.get("KEYCLOAK_URL")
        self.keycloak_admin = os.environ.get("KC_BOOTSTRAP_ADMIN_USERNAME")
        self.keycloak_admin_password = os.environ.get("KC_BOOTSTRAP_ADMIN_PASSWORD")
        self.keycloak_app_realm_name = os.environ.get("KEYCLOAK_APP_REALM_NAME")
        self.keycloak_app_client_name = os.environ.get("KEYCLOAK_APP_CLIENT_NAME")
        self.keycloak_app_admin_group_name = os.environ.get(
            "KEYCLOAK_APP_ADMIN_GROUP_NAME"
        )
        self.keycloak_app_admin_username = os.environ.get("KEYCLOAK_APP_ADMIN_USERNAME")
        self.keycloak_app_admin_password = os.environ.get("KEYCLOAK_APP_ADMIN_PASSWORD")
        self.keycloak_app_admin_email = os.environ.get("KEYCLOAK_APP_ADMIN_EMAIL")


class KeycloakClient(KeycloakConfig):
    """
    Keycloak client class used to create the Keycloak admin entries for the app
    """

    def __init__(self):
        """
        Initializes the Keycloak client
        """
        super().__init__()
        self.access_token = None
        self.app_admin_group_id = None

    def get_access_token(self):
        """
        Gets the access token for the Keycloak admin user
        """
        response = requests.post(
            f"{self.keycloak_url}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": self.keycloak_admin,
                "password": self.keycloak_admin_password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.access_token = response.json()["access_token"]

    def create_realm(self):
        """
        Creates the Keycloak realm for the app
        """
        # Check if the realm already exists
        existing_realm = None
        response = requests.get(
            f"{self.keycloak_url}/admin/realms",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code == 200:
            realms = response.json()
            existing_realm = next(
                (
                    realm
                    for realm in realms
                    if realm["realm"] == self.keycloak_app_realm_name
                ),
                None,
            )
        else:
            raise Exception(
                f"Failed to retrieve realms. Status code: {response.status_code}"
            )

        if existing_realm:
            # Realm already exists, return its ID
            print(f"Realm '{self.keycloak_app_realm_name}' already exists.")
        else:
            # Realm does not exist, create it
            print(f"Creating new realm: {self.keycloak_app_realm_name}...")
            response = requests.post(
                f"{self.keycloak_url}/admin/realms",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={"realm": self.keycloak_app_realm_name, "enabled": True},
            )
            if response.status_code == 201:
                print(f"Realm '{self.keycloak_app_realm_name}' created successfully.")
            else:
                print(f"Failed to create realm. Status code: {response.status_code}")

    def create_client(self):
        """
        Creates the Keycloak client for the app in the app realm
        """
        # Check if client already exists
        client_exists = False
        response = requests.get(
            f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/clients",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code == 200:
            clients = response.json()
            for client in clients:
                if client["clientId"] == self.keycloak_app_client_name:
                    client_exists = True
        else:
            raise Exception(
                f"Failed to retrieve clients. Status code: {response.status_code}"
            )
        if client_exists:
            print(f"Client '{self.keycloak_app_client_name}' already exists.")
        else:
            # Client does not exist, create it
            print(f"Creating new client: {self.keycloak_app_client_name}...")
            response = requests.post(
                f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/clients",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "clientId": self.keycloak_app_client_name,
                    "enabled": True,
                    "redirectUris": ["http://localhost:8080/*"],
                },
            )
            if response.status_code == 201:
                print(f"Client '{self.keycloak_app_client_name}' created successfully.")
            else:
                print(f"Failed to create client. Status code: {response.status_code}")

    def create_group(self):
        """
        Creates the Keycloak group for the app in the app realm
        """

        # Check if group already exists
        def check_group_exists():
            """
            Checks if the group already exists and returns its ID to self.app_admin_group_id if it does in the app realm
            """
            group_exists = False
            response = requests.get(
                f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/groups",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
            )
            if response.status_code == 200:
                groups = response.json()
                for group in groups:
                    if group["name"] == self.keycloak_app_admin_group_name:
                        group_exists = True
                        self.app_admin_group_id = group["id"]
            else:
                raise Exception(
                    f"Failed to retrieve groups. Status code: {response.status_code}"
                )
            return group_exists

        if check_group_exists():
            print(f"Group '{self.keycloak_app_admin_group_name}' already exists.")
        else:
            # Group does not exist, create it
            print(f"Creating new group: {self.keycloak_app_admin_group_name}...")
            response = requests.post(
                f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/groups",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": self.keycloak_app_admin_group_name,
                },
            )
            if response.status_code == 201:
                check_group_exists()
                print(
                    f"Group '{self.keycloak_app_admin_group_name}' created successfully."
                )
            else:
                print(f"Failed to create group. Status code: {response.status_code}")

    def assign_admin_roles_to_group(self):
        """
        Assigns the admin roles(realm and client) to the group in the app realm
        """
        # Get the realm roles which are available/yet to be assigned to the group
        # Note: if there are no roles available, then it would mean that they are already assigned
        realm_roles_to_assign = []
        response = requests.get(
            f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/groups/{self.app_admin_group_id}/role-mappings/realm/available?first=0&max=100",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code == 200:
            realm_roles = response.json()
            for realm_role in realm_roles:
                realm_roles_to_assign.append(
                    {
                        "id": realm_role["id"],
                        "name": realm_role["name"],
                        "description": realm_role["description"],
                    }
                )
        else:
            raise Exception(
                f"Failed to retrieve realm roles. Status code: {response.status_code}"
            )

        # Get the client roles which are available/yet to be assigned to the group
        # Note: if there are no roles available, then it would mean that they are already assigned
        client_roles_to_assign = []
        response = requests.get(
            f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/ui-ext/available-roles/groups/{self.app_admin_group_id}/?first=0&max=1000",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code == 200:
            client_roles = response.json()
            for client_role in client_roles:
                client_roles_to_assign.append(
                    {
                        "id": client_role["id"],
                        "name": client_role["role"],
                        "description": client_role["description"],
                        "client_id": client_role["clientId"],
                    }
                )
        else:
            raise Exception(
                f"Failed to retrieve client roles. Status code: {response.status_code}"
            )

        if realm_roles_to_assign:
            # Assign the roles to the group
            print(
                f"Assigning roles '{realm_roles_to_assign}' to group '{self.keycloak_app_admin_group_name}'..."
            )
            response = requests.post(
                f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/groups/{self.app_admin_group_id}/role-mappings/realm",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=realm_roles_to_assign,
            )
            if response.status_code == 204:
                print(
                    f"Roles '{realm_roles_to_assign}' assigned to group '{self.keycloak_app_admin_group_name}' successfully"
                )
            else:
                print(
                    f"Failed to assign roles to group. Status code: {response.status_code}"
                )
        else:
            print(
                f"No realm roles to assign to group, they should already be assigned to group '{self.keycloak_app_admin_group_name}'"
            )

        if client_roles_to_assign:
            # Assign the client roles to the group
            print(
                f"Assigning client roles to group '{self.keycloak_app_admin_group_name}'..."
            )
            for client_role in client_roles_to_assign:
                client_id = client_role.pop("client_id")
                response = requests.post(
                    f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/groups/{self.app_admin_group_id}/role-mappings/clients/{client_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=[client_role],
                )
                if response.status_code == 204:
                    print(
                        f"Client role {client_role} assigned to group '{self.keycloak_app_admin_group_name}' successfully"
                    )
                else:
                    print(
                        f"Failed to assign client role {client_role} to group '{self.keycloak_app_admin_group_name}'. Status code: {response.status_code}"
                    )
        else:
            print(
                f"No client roles to assign to group, they should already be assigned to group '{self.keycloak_app_admin_group_name}'"
            )

    def create_user(self):
        """
        Creates the Keycloak admin user for the app in the app realm
        """
        # Check if user already exists
        user_exists = False
        response = requests.get(
            f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/users",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user["username"] == self.keycloak_app_admin_username:
                    user_exists = True
                    print(f"User '{self.keycloak_app_admin_username}' already exists")
                    return

        # User does not exist, create it
        if not user_exists:
            print(f"Creating user '{self.keycloak_app_admin_username}'...")
            response = requests.post(
                f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/users",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "username": self.keycloak_app_admin_username,
                    "enabled": True,
                    "email": self.keycloak_app_admin_email,
                    "emailVerified": True,
                    "credentials": [
                        {
                            "type": "password",
                            "value": self.keycloak_app_admin_password,
                            "temporary": False,
                        }
                    ],
                },
            )
            if response.status_code == 201:
                print(f"User '{self.keycloak_app_admin_username}' created successfully")
            else:
                print(
                    f"Failed to create user '{self.keycloak_app_admin_username}'. Status code: {response.status_code}"
                )

    def add_user_to_group(self):
        """
        Adds the app admin user to the app admin group in the app realm
        """
        users_to_add_to_group = []
        response = requests.get(
            f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/users?first=0&max=1000",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code == 200:
            users = response.json()
            for user in users:
                users_to_add_to_group.append(
                    {
                        "id": user["id"],
                        "username": user["username"],
                    }
                )
        else:
            raise Exception(
                f"Failed to retrieve realm roles. Status code: {response.status_code}"
            )

        if users_to_add_to_group:
            for user in users_to_add_to_group:
                response = requests.put(
                    f"{self.keycloak_url}/admin/realms/{self.keycloak_app_realm_name}/users/{user['id']}/groups/{self.app_admin_group_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                if response.status_code == 204:
                    print(
                        f"User '{user['username']}' added to '{self.keycloak_app_admin_group_name}' successfully"
                    )
                else:
                    print(
                        f"Failed to add user '{user['username']}' to '{self.keycloak_app_admin_group_name}'. Status code: {response.status_code}"
                    )
        else:
            print(
                f"No users to add to group, they should already be added to group '{self.keycloak_app_admin_group_name}'"
            )


if __name__ == "__main__":
    keycloak_client = KeycloakClient()
    keycloak_client.get_access_token()

    keycloak_client.create_realm()
    keycloak_client.create_client()

    keycloak_client.create_group()
    keycloak_client.assign_admin_roles_to_group()

    keycloak_client.create_user()
    keycloak_client.add_user_to_group()
