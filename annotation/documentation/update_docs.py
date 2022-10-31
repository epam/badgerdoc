import yaml

from app.main import app


def str_presenter(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar(
            "tag:yaml.org,2002:str", data, style="|"
        )
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)


def save_openapi_yaml():
    openapi_data = app.openapi()
    with open("documentation/openapi.yaml", "w") as file:
        yaml.dump(openapi_data, file, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    save_openapi_yaml()
