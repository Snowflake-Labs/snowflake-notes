import http.client
import json
import urllib.request
import http.cookiejar
import sys

from auth import creds
from dashboards import dashboard_list


def login(account_name, username, password):
    # Data to be sent in the request body
    data = {
        "data": {
            "ACCOUNT_NAME": account_name,
            "LOGIN_NAME": username,
            "PASSWORD": password,
            "CLIENT_APP_ID": "Snowflake UI",
            "CLIENT_APP_VERSION": 20231219004219,
        }
    }

    # Convert the data to JSON
    data_json = json.dumps(data).encode("utf-8")

    # Headers
    headers = {
        "Content-Type": "application/json",
    }

    # Create a connection - replace with proxy details if needed
    url = f"https://{account_name}.snowflakecomputing.com/session/v1/login-request?__uiAppName=Login"

    req = urllib.request.Request(url, data=data_json, headers=headers, method="POST")

    # Perform the request and extract the 'redirectURI'
    try:
        with urllib.request.urlopen(req) as response:
            print(response)
            response_data = json.loads(response.read().decode())
            return response_data["data"]["redirectURI"]

    except urllib.error.URLError as e:
        print(e.reason)


def complete_oauth(redirect_url, account_name):
    """
    Completes the OAuth flow, returning the cookies as a string that can be used to authenticate with Snowsight.

    Args:
        redirect_url: The redirect URL returned from the login request
        account_name: The Snowflake account name
        region: The Snowflake region (us-east-1, etc)

    Returns:
        Cookies, as a string, to use for authentication in Snowsight.
    """

    # Create a cookie jar to handle cookies, as Pythons urllib does not handle multiple headers
    # with the same name well..
    cookie_jar = http.cookiejar.CookieJar()

    # Create an opener that will use the cookie jar
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    url = f"{redirect_url}&state=%7B%22url%22%3A%22https%3A%2F%2F{account_name}.snowflakecomputing.com%22%7D"

    # Open the URL, we don't care about the response, we just want the cookies.
    opener.open(url)

    # Extract cookies from the cookie jar
    cookies = []

    # Display the extracted cookies
    for cookie in [cookie for cookie in cookie_jar]:
        cookies.append(cookie.name + "=" + cookie.value)

    return "; ".join(cookies)


def snowsight_bootstrap(account_name, region, username, cookies):
    """
    Snowflake requires an `OrganizationID` and `csrfToken` for Snowsight endpoints, which you can retrieve
    from the `bootstrap` endpoint.

    Args:
        account_name: The Snowflake account name
        region: The Snowflake region (us-east-1, etc)
        username: The username to login with
        cookies: The list of cookies to use for authentication

    Returns:
        A dict containing the `OrganizationID` and `csrfToken` for the Snowflake account.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-Snowflake-Context": f"{username.upper()}::https://{account_name}.snowflakecomputing.com",
        "Cookie": cookies,
    }

    # Create a connection - replace with proxy details if needed
    url = f"https://apps-api.c1.{region}.aws.app.snowflake.com/bootstrap"

    req = urllib.request.Request(url, headers=headers, method="GET")

    # Perform the request and extract the 'redirectURI'
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode())
            csrf_token = response_data["PageParams"]["csrfToken"]

            # `OrganizationID` is from either:
            #
            # 1. response_data["Org"]["id"].
            # 2. That value can be null/empty, fall back to response_data["User"]["defaultOrgId"]
            org_id = response_data["Org"]["id"] or response_data["User"]["defaultOrgId"]

            return {"csrf_token": csrf_token, "org_id": org_id}

    except urllib.error.URLError as e:
        print(e.reason)


def refresh_dashboard(account_name, username, dashboard_id, csrf_token, cookies):
    """
    Refreshes dashboards.

    Args:
        account_name: The Snowflake account name
        username: The username to use
        csrf_token: The csrfToken to use
        cookies: The list of cookies to use for authentication

    Returns:
        A dict containing the `OrganizationID` and `csrfToken` for the Snowflake account.
    """

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRF-Token": csrf_token,
        "X-Snowflake-Context": f"{username.upper()}::https://{account_name}.snowflakecomputing.com",
        "Cookie": cookies,
    }

    # Create a connection - replace with proxy details if needed
    # url = f"https://apps-api.c1.{region}.aws.app.snowflake.com/v0/organizations/{org_id}/entities/list"
    url = (
        f"https://apps-api.c1.us-west-2.aws.app.snowflake.com/v0/folders/{dashboard_id}"
    )

    req = urllib.request.Request(
        url,
        headers=headers,
        method="POST",
        data="action=refresh&drafts={}".encode("utf-8"),
    )
    print(f"Refreshing dashboad with ID {dashboard_id}")

    # Perform the request and extract all queries.
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode())
            return response_data

    except urllib.error.URLError as e:
        print(e.reason)


# if __name__ == "__main__":
sf_account = creds.account
sf_region = creds.region
sf_username = creds.username
sf_password = creds.password

print(f"Account name: {sf_account}, Region: {sf_region} Username: {sf_username}")

print("Attempting to login.")
returned_redirect_url = login(sf_account, sf_username, sf_password)
print(f"Logged in, Redirect URL - {returned_redirect_url}")

print("Completing OAuth Request")
returned_cookies = complete_oauth(returned_redirect_url, sf_account)
print(f"Completed OAuth - Cookies - {returned_cookies}")

print("Bootstrapping")
bootstrap_data = snowsight_bootstrap(
    sf_account, sf_region, sf_username, returned_cookies
)
print(f"Bootstrap returned - {bootstrap_data}")

for d in dashboard_list:
    dashboards = refresh_dashboard(
        sf_account,
        sf_username,
        d,
        bootstrap_data["csrf_token"],
        returned_cookies,
    )
