from pathlib import Path
import sys
import os

# 先定义一些基本路径，因为config模块会依赖这些路径
def get_application_path():
    """
    获取应用程序的实际路径，兼容不同的运行环境
    """
    if hasattr(sys, 'frozen'):
        # 对于打包后的环境，返回可执行文件所在目录
        return Path(os.path.dirname(sys.executable))
    else:
        # 开发环境
        return Path(__file__).resolve().parent.parent

# 获取应用程序目录
PROJECT_DIR = get_application_path()

RESOURCE_DIR = PROJECT_DIR / "Resource"
LOGO_FILE = PROJECT_DIR / "Resource" / "logo.ico"
LOL_OUT_DIR = PROJECT_DIR / "LOL_OUT"
LOL_CLIENT_DIR = ""
LOG_FILE = PROJECT_DIR / "log.log"
CONFIG_FILE = PROJECT_DIR / "config.json"

# 定义默认路径
def get_lol_out_dir():
    return LOL_OUT_DIR

def get_lol_client_dir():
    return LOL_CLIENT_DIR

# 哈希表相关路径
DEFAULT_CDTB_HASHES_DIR = PROJECT_DIR /  "hashes" / "cdtb_hashes"
DEFAULT_EXTRACTED_HASHES_DIR = PROJECT_DIR /  "hashes" / "extracted_hashes"
DEFAULT_CUSTOM_HASHES_DIR = PROJECT_DIR /  "hashes" / "custom_hashes"

# 获取哈希表路径函数
def get_cdtb_hashes_dir():
    return DEFAULT_CDTB_HASHES_DIR

def get_extracted_hashes_dir():
    return DEFAULT_EXTRACTED_HASHES_DIR

def get_custom_hashes_dir():
    return DEFAULT_CUSTOM_HASHES_DIR


# 导入配置并读取路径设置
try:
    # 延迟导入，避免循环依赖
    from .config import cfg
    
    # 确保配置已加载
    if hasattr(cfg, 'load') and callable(cfg.load):
        try:
            cfg.load()
        except Exception:
            pass
    
    # 从配置中获取路径，如果配置不存在则使用默认值
    def get_path_from_config(config_item, default_func):
        # 检查配置是否已加载并且有效
        try:
            # 直接获取配置项的值（qfluentwidgets的ConfigItem行为）
            if hasattr(config_item, 'value'):
                path_str = str(config_item.value)
            else:
                path_str = str(config_item)
            
            if path_str and not path_str.startswith('ConfigItem'):
                # 如果是相对路径，转换为绝对路径
                path = Path(path_str)
                if not path.is_absolute():
                    path = PROJECT_DIR / path
                return path.resolve()
        except (AttributeError, TypeError, ValueError, Exception):
            pass
        return default_func()
    
    # 从配置中获取路径
    LOL_OUT_DIR = get_path_from_config(cfg.lol_out_dir, get_lol_out_dir)
    LOL_CLIENT_DIR = get_path_from_config(cfg.lol_client_dir, get_lol_client_dir)
    
    # 从配置中获取哈希表路径
    DEFAULT_CDTB_HASHES_DIR = get_path_from_config(cfg.cdtb_hashes_dir, get_cdtb_hashes_dir)
    DEFAULT_EXTRACTED_HASHES_DIR = get_path_from_config(cfg.extracted_hashes_dir, get_extracted_hashes_dir)
    DEFAULT_CUSTOM_HASHES_DIR = get_path_from_config(cfg.custom_hashes_dir, get_custom_hashes_dir)

    
except ImportError:
    # 如果无法导入配置，使用默认路径
    LOL_OUT_DIR = get_lol_out_dir()
    LOL_CLIENT_DIR = get_lol_client_dir()
    DEFAULT_CDTB_HASHES_DIR = get_cdtb_hashes_dir()
    DEFAULT_EXTRACTED_HASHES_DIR = get_extracted_hashes_dir()
    DEFAULT_CUSTOM_HASHES_DIR = get_custom_hashes_dir()




