import upstox_client
from app.db.postgres import PostgresClient

class UpstoxAuthService:
    @staticmethod
    async def save_credentials(api_key: str, api_secret: str, redirect_uri: str):
        pool = PostgresClient.get_pool()
        async with pool.acquire() as conn:
            # Upsert credentials (assuming single user for now, ID=1)
            await conn.execute("""
                INSERT INTO credentials (id, api_key, api_secret, redirect_uri)
                VALUES (1, $1, $2, $3)
                ON CONFLICT (id) DO UPDATE 
                SET api_key = EXCLUDED.api_key,
                    api_secret = EXCLUDED.api_secret,
                    redirect_uri = EXCLUDED.redirect_uri,
                    updated_at = CURRENT_TIMESTAMP
            """, api_key, api_secret, redirect_uri)

    @staticmethod
    async def get_credentials():
        pool = PostgresClient.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM credentials WHERE id = 1")

    @staticmethod
    async def get_login_url() -> str:
        creds = await UpstoxAuthService.get_credentials()
        if not creds:
            raise ValueError("Credentials not configured")
            
        api_key = creds['api_key']
        redirect_uri = creds['redirect_uri']
        
        # Construct URL manually to avoid SDK complexity for simple redirect
        return f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}"

    @staticmethod
    async def generate_access_token(code: str):
        creds = await UpstoxAuthService.get_credentials()
        if not creds:
            raise ValueError("Credentials not configured")

        api_key = creds['api_key']
        api_secret = creds['api_secret']
        redirect_uri = creds['redirect_uri']

        # Use SDK to get token
        configuration = upstox_client.Configuration()
        api_instance = upstox_client.LoginApi(upstox_client.ApiClient(configuration))
        
        try:
            api_response = api_instance.token(
                api_version='2.0',
                code=code,
                client_id=api_key,
                client_secret=api_secret,
                redirect_uri=redirect_uri,
                grant_type='authorization_code'
            )
            
            access_token = api_response.access_token
            
            # Save token to DB
            pool = PostgresClient.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE credentials 
                    SET access_token = $1, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = 1
                """, access_token)
                
            return access_token
        except Exception as e:
            raise RuntimeError(f"Failed to generate token: {e}")
