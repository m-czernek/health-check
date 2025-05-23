"""
Module that contains functionality related to reading `config.toml`
and getting paths used for configuration, templating, or building
containers
"""

import functools
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

import jinja2
import tomli

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_CONFIG_DIR = os.path.join(BASE_DIR, "config")
TEMPLATES_DIR = os.path.join(SOURCE_CONFIG_DIR, "templates")
CONTAINERS_DIR = os.path.join(BASE_DIR, "containers")
CONFIG_TOML_PATH = os.environ.get(
    "HEALTH_CHECK_TOML", os.path.join(BASE_DIR, "config.toml")
)
GENERATED_CONFIG_DIR = os.path.expanduser("~/.local/share/health_check/")


@functools.lru_cache
def _init_jinja_env() -> jinja2.Environment:
    return jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES_DIR))


@functools.lru_cache
def parse_config() -> Dict:
    if not os.path.exists(CONFIG_TOML_PATH):
        raise ValueError(f"Config file does not exist: {CONFIG_TOML_PATH}")

    with open(CONFIG_TOML_PATH, "rb") as f:
        conf = tomli.load(f)
    return conf


def get_json_template_filepath(json_relative_path: str) -> str:
    return os.path.join(TEMPLATES_DIR, json_relative_path)


def load_jinja_template(template: str) -> jinja2.Template:
    return _init_jinja_env().get_template(template)


def get_config_sources_dir_path(component: str) -> str:
    return os.path.join(SOURCE_CONFIG_DIR, component)


def get_config_dir_path(component: str) -> str:
    return os.path.join(GENERATED_CONFIG_DIR, component)


def load_prop(property_path: str) -> Any:
    res = parse_config().copy()
    for prop_part in property_path.split("."):
        try:
            res = res[prop_part]
        except Exception as e:
            raise ValueError(
                f"Invalid config lookup ({property_path}); trying to get {prop_part} from {res}"
            ) from e
    return res


def copy_config_sources(component: str):
    """
    Copy config sources for a compontent to the GENERATED_CONFIG_DIR
    """
    source_basedir = get_config_sources_dir_path(component)
    target_basedir = Path(get_config_dir_path(component))
    if target_basedir.exists():
        shutil.rmtree(target_basedir)
    shutil.copytree(source_basedir, target_basedir)


def write_config(component: str, config_file_path: str, content: str, is_json=False):
    """
    Store configuration content into config_file_path relative
    to GENERATED_CONFIG_DIR
    """
    basedir = Path(get_config_dir_path(component))
    if not basedir.exists():
        basedir.mkdir(parents=True)
    file_path = os.path.join(basedir, config_file_path)
    with open(file_path, "w", encoding="UTF-8") as file:
        if is_json:
            json.dump(content, file, indent=4)
        else:
            file.write(content)


def clean_config():
    """
    Remove all possible health check generated directories
    containing config files under GENERATED_CONFIG_DIR
    """
    if os.path.exists(GENERATED_CONFIG_DIR):
        shutil.rmtree(GENERATED_CONFIG_DIR)


def get_config_file_path(component: str) -> str:
    return os.path.join(get_config_dir_path(component), "config.yaml")


def get_sources_dir(component: str) -> str:
    return os.path.join(BASE_DIR, component)


def get_all_container_image_names() -> List[str]:
    res = []
    conf = parse_config().copy()
    for section in conf.values():
        if "image" in section:
            res.append(section.get("image"))
    return res
