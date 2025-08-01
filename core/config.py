import os
import yaml
from loguru import logger
from rich import print as rprint


# Config
class Config:
    def __init__(self):
        self.config_path = 'config.yaml'
        self.is_config_not_exist = False
        self.config = self.read_config()

        # read user config
        self.version: float = self.get("nk_app", {}).get("version", "1.0")
        self.lang: str = self.get("nk_app", {}).get("lang", "en")
        self.score_dir: str = self.get("user_config", {}).get("score_dir", "")
        self.global_bpm: int = self.get("user_config", {}).get("bpm", 120)
        self.beat: int = self.get("user_config", {}).get("beat", 4)
        self.enable_key: str = self.get("user_config", {}).get("enable_key", "C")
        self.exit_key: str = self.get("user_config", {}).get("exit_key", "ESC")
        self.hold_threshold: float = self.get("user_config", {}).get("hold_threshold", 0.05)
        self.debug: bool = self.get("user_config", {}).get("debug", False)

        # key_mapping
        self.key_mapping: dict = self._key_mapping_(self.get("user_config", {}).get("key_bind", []))

    def read_config(self) -> dict:
        ''''
        读取配置文件
        '''
        # make sure config file exists
        if not os.path.exists(self.config_path):
            self.is_config_not_exist = True
            logger.warning(f"Config file not found: {self.config_path}")
            rprint("正在创建默认配置文件...")
            logger.info("Creating default config file...")
            if create_config():
                rprint("请在运行程序前修改配置文件。")
                logger.info("Please modify the config file before running the program again.")
                return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data
        except Exception:
            logger.error(f"Failed to read config file: {self.config_path}")
            return {}

    def _key_mapping_(self, key_bind: list) -> dict:
        """"
        键位映射
        """
        _to_number_ = {
            'do': '1', 're': '2', 'mi': '3', 'fa': '4',
            'so': '5', 'la': '6', 'ti': '7',
            'do#': '1#', 're#': '2#', 'mi#': '3#', 'fa#': '4#',
            'so#': '5#', 'la#': '6#', 'ti#': '7#',
            'do/': '1/', 're/': '2/', 'mi/': '3/', 'fa/': '4/',
            'so/': '5/', 'la/': '6/', 'ti/': '7/',
        }

        mapping = {}

        try:
            for bind in key_bind:
                if isinstance(bind, dict):
                    for solfege, key in bind.items():
                        mapping[solfege] = key
                        if solfege in _to_number_:
                            mapping[_to_number_[solfege]] = key
        except Exception as e:
            logger.error(f"键位映射错误: {str(e)}")
            return {}

        return mapping

    def get(self, key, default=None) -> dict:
        return self.config.get(key, default)


def create_config() -> bool:
    """"
    创建默认配置文件
    """
    DEFAULT_CONFIG = {
        'nk_app': {
            'version': 1.0,
            # cn, en
            'lang': 'cn'
        },
        'user_config': {
            'score_dir': '/score',
            'global_bpm': 120,
            'beat': 4,
            'hold_threshold': 0.05,
            'enable_key': 'C',
            'exit_key': 'ESC',
            'play_interrupt': False,
            'debug': False,
            'key_bind': [
                {'do': 'a'}, {'re': 's'}, {'mi': 'd'},
                {'fa': 'f'}, {'so': 'g'}, {'la': 'h'},
                {'ti': 'j'}, {'do#': 'q'}, {'re#': 'w'},
                {'mi#': 'e'}, {'fa#': 'r'}, {'so#': 't'},
                {'la#': 'y'}, {'ti#': 'u'},
                {'do/': 'z'}, {'re/': 'x'}, {'mi/': 'c'},
                {'fa/': 'v'}, {'so/': 'b'}, {'la/': 'n'},
                {'ti/': 'm'},
                {'sharp': 'shift'}
            ]
        }
    }
    try:
        os.makedirs(os.path.dirname(os.path.abspath('config.yaml')), exist_ok=True)
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                DEFAULT_CONFIG,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False
            )
        logger.success("Created default config file: config.yaml")
        return True
    except Exception as e:
        logger.error(f"Failed to create default config file: {str(e)}")
        return False
