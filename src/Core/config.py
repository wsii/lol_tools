from pathlib import Path

from qfluentwidgets import (
    ConfigItem,
    QConfig
)

from .paths import (
    CONFIG_FILE, 
    get_lol_out_dir, 
    get_lol_client_dir,
    get_cdtb_hashes_dir,
    get_extracted_hashes_dir,
    get_custom_hashes_dir
)

class Config(QConfig):
    
    # 添加LOL相关路径配置
    lol_out_dir = ConfigItem("Paths", "导出资产路径", str(get_lol_out_dir()))
    lol_client_dir = ConfigItem("Paths", "LOL客户端资产路径", str(get_lol_client_dir()))
    
    # 添加哈希表相关配置
    cdtb_hashes_dir = ConfigItem("HashTables", "CDTB哈希路径", str(get_cdtb_hashes_dir()))
    extracted_hashes_dir = ConfigItem("HashTables", "提取哈希路径", str(get_extracted_hashes_dir()))
    custom_hashes_dir = ConfigItem("HashTables", "自定义哈希路径", str(get_custom_hashes_dir()))

# 创建配置实例
cfg = Config()
cfg.file = CONFIG_FILE
if not CONFIG_FILE.exists():
    cfg.save()
QConfig.load(CONFIG_FILE, cfg)
