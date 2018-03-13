import os, json, subprocess
from contextlib import contextmanager
from tempfile import mkdtemp


config = {}


def debug(*args, **kwargs):
    if os.environ.get("DPP_DEBUG"):
        print(*args, **kwargs)


def os_system_generator(command):
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        yield line.decode('utf-8')


def os_system(command):
    if os.environ.get("DPP_DEBUG"):
        return os.system(command)
    else:
        return os.system("( {} ) >/dev/null 2>&1".format(command))


def get_etc_path():
    return os.environ.get("DPP_PLAYGROUND_ETC_PATH", "/etc/dpp-playground")


def get_config_file():
    config_file = os.path.join(get_etc_path(), "config.json")
    debug("config_file={}".format(config_file))
    return config_file


def get_config():
    config_file = get_config_file()
    if os.path.exists(config_file):
        with open(config_file) as f:
            config.update(**json.loads(f.read()))
    return config


def set_config(key, value):
    get_config()
    config.update(**{key: value})
    config_file = get_config_file()
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(config, f)


def get_service_account_json_file_path():
    return os.path.join(get_etc_path(), "secret.json")


@contextmanager
def temp_dir(*args, **kwargs):
    dir = mkdtemp(*args, **kwargs)
    try:
        yield dir
    except Exception:
        if os.path.exists(dir):
            os.rmdir(dir)
        raise


@contextmanager
def temp_file(*args, **kwargs):
    with temp_dir(*args, **kwargs) as dir:
        file = os.path.join(dir, "temp")
        try:
            yield file
        except Exception:
            if os.path.exists(file):
                os.unlink(file)
            raise
