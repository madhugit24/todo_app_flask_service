from datetime import datetime
import json
import hvac
import os


class VaultClient:
    def __init__(self, url, token):
        """
        Initializes the Vault client
        """
        self.client = hvac.Client(url=url, token=token)

    def create_secret_engine(self, name, type):
        """
        Creates a new secret engine
        """
        # Check if the secret engine already exists
        response = self.client.sys.list_mounted_secrets_engines()
        if any(engine == f"{name}/" for engine in response):
            print(f"Secret engine '{name}' already exists!")
        else:
            # Create a new secret engine
            response = self.client.sys.enable_secrets_engine(
                path=name, backend_type=type, description=f"{name} secrets engine"
            )
            if response.status_code == 204:
                print(f"Secret engine '{name}' created successfully!")
            else:
                print(f"Error creating secret engine: {response.text}")

    def create_policy(self, name, policy):
        """
        Creates a new policy
        """
        # Check if the policy already exists
        response = self.client.sys.list_policies()
        if name in response["data"]["policies"]:
            print(f"Policy '{name}' already exists!")
        else:
            # Create a new policy
            response = self.client.sys.create_or_update_policy(name=name, policy=policy)
            if response.status_code == 204:
                print(f"Policy '{name}' created successfully!")
            else:
                print(f"Error creating policy: {response.text}")

    def create_auth_method(self, name):
        """
        Creates a new auth method
        """
        # Check if the auth method already exists
        response = self.client.sys.list_auth_methods()
        if f"{name}/" in response.keys():
            print(f"Auth method '{name}' already exists!")
        else:
            # Create a new auth method
            response = self.client.sys.enable_auth_method(
                path=name, method_type="userpass"
            )
            if response.status_code == 204:
                print(f"Auth method '{name}' created successfully!")
            else:
                print(f"Error creating auth method: {response.text}")

    def create_user(self, username, password, policy_name, auth_method_name):
        """
        Creates a new user
        """

        def __create_user(username, password, policy_name, auth_method_name):
            """ "
            Creates a new user
            """
            response = self.client.auth.userpass.create_or_update_user(
                username=username,
                password=password,
                policies=policy_name,
                mount_point=auth_method_name,
            )
            if response.status_code == 204:
                print(f"User '{username}' created successfully!")
            else:
                print(f"Error creating user: {response.text}")

        # Check if the user already exists
        try:
            response = self.client.auth.userpass.list_user(mount_point=auth_method_name)
            if username in response["data"]["keys"]:
                print(f"User '{username}' already exists!")
            else:
                # Create a new user
                __create_user(username, password, policy_name, auth_method_name)
        except Exception as e:
            print(f"Error listing users: {e}")
            # Create a new user
            __create_user(username, password, policy_name, auth_method_name)


class VaultConfig:

    def __init__(
        self,
        url,
        shares,
        threshold,
        secret_engine_name,
        policy_name,
        auth_method_name,
        user_name,
        password,
    ):
        self.url = url
        self.token = None
        self.keys = None
        self.keys_base64 = None
        self.shares = shares
        self.threshold = threshold
        self.secret_engine_name = secret_engine_name
        self.policy_name = policy_name
        self.auth_method_name = auth_method_name
        self.user_name = user_name
        self.password = password

    def initialize_and_unseal_vault(self):
        """
        Initializes and Unseals the vault server
        """
        client = hvac.Client(url=self.url)
        print(
            f"Initializing and Unsealing the vault server... is_initialized: {client.sys.is_initialized()}"
        )
        if not client.sys.is_initialized():
            result = client.sys.initialize(self.shares, self.threshold)
            self.token = result["root_token"]
            self.keys = result["keys"][0]
            self.keys_base64 = result["keys_base64"][0]
            print(
                f"Initializing and Unsealing the vault server... is_initialized after init: {client.sys.is_initialized()}"
            )
            # Dump token and keys into a JSON file
            current_date = datetime.now().strftime("%d%m%Y")
            filename = f"vault_root_creds_{current_date}.json"
            data = {
                "token": self.token,
                "keys": self.keys,
                "keys_base64": self.keys_base64,
            }
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Token and keys dumped to {filename}")
        else:
            self.token = os.environ.get("VAULT_TOKEN", "")
            self.keys = os.environ.get("VAULT_KEYS", "")
            self.keys_base64 = os.environ.get("VAULT_KEYS_BASE64", "")
        print(
            f"Initializing and Unsealing the vault server... is_sealed after init before unseal: {client.sys.is_sealed()}"
        )
        if client.sys.is_sealed():
            unseal_response = client.sys.submit_unseal_keys([self.keys_base64])
            print(unseal_response)
            print(
                f"Initializing and Unsealing the vault server... is_sealed after init after unseal: {client.sys.is_sealed()}"
            )

    def configure_vault(self):
        """
        Configures the vault server with the required secret engine, policy, auth method and user
        """
        client = VaultClient(self.url, self.token)
        client.create_secret_engine(self.secret_engine_name, "kv")
        client.create_policy(self.policy_name, self.get_policy())
        client.create_auth_method(self.auth_method_name)
        client.create_user(
            self.user_name, self.password, self.policy_name, self.auth_method_name
        )

    def get_policy(self):
        """
        Returns a Vault Policy with permissions for the vault secret engine
        """
        return f"""
                path "{self.secret_engine_name}/*" {{
                capabilities = ["create", "read", "update", "delete", "list"]
                }}
                """


if __name__ == "__main__":
    config = VaultConfig(
        url=os.environ.get("VAULT_URL", "http://localhost:8200"),
        shares=int(os.environ.get("VAULT_SHARES", "1")),
        threshold=int(os.environ.get("VAULT_THRESHOLD", "1")),
        secret_engine_name=os.environ.get("VAULT_SECRET_ENGINE_NAME", ""),
        policy_name=os.environ.get("VAULT_POLICY_NAME", ""),
        auth_method_name=os.environ.get("VAULT_AUTH_METHOD_NAME", ""),
        user_name=os.environ.get("VAULT_USER_NAME", ""),
        password=os.environ.get("VAULT_USER_PASSWORD", ""),
    )
    config.initialize_and_unseal_vault()
    config.configure_vault()
