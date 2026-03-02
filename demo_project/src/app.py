"""Demo application entrypoint."""

# TODO: add request-id middleware for distributed tracing

from demo_project.src.service import create_user, get_user


def run_demo() -> None:
    result = create_user({"name": "Alice", "external_id": "ext-001"})
    print("create_user:", result)

    if result.get("user"):
        user_id = result["user"]["id"]
        found = get_user(user_id)
        print("get_user:", found)


if __name__ == "__main__":
    run_demo()
