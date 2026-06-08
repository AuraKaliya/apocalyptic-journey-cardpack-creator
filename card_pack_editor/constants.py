APP_TITLE = "Witch's Apocalyptic Journey - Card Pack Editor"

CARD_DATA_HEADER = [
    "Id", "Rarity", "Expend", "Tag", "PackBelong", "InitScript",
    "DrawScript", "UseScript", "DropScript", "Icon", "Effects", "Action",
]
CARD_DATA_COMMENT = [
    "唯一标识", "稀有度", "花费", "标签", "所属卡包", "更新显示信息用的",
    "卡牌抽到后执行", "卡牌使用后执行", "卡牌进入弃牌堆后执行", "图标资源的路径", "特效路径", "动作",
]

CARD_TEXT_HEADER = [
    "Id", "是否完成", "Type", "Note", "Name", "Name_en", "Name_zh-Hant",
    "Name_ja", "Description", "Description_zh-Hant", "Description_en", "Description_ja",
]
CARD_TEXT_COMMENT = [
    "唯一标识", "FALSE", "类型", "备注", "名称", "Name", "名稱",
    "名称", "描述", "描述", "Description", "説明",
]

CARDPACK_DATA_HEADER = ["Id", "Type", "Icon"]
CARDPACK_DATA_COMMENT = ["唯一标识", "卡包类型", "卡包图标"]
CARDPACK_TEXT_HEADER = [
    "Id", "Note", "Name", "Name_zh-Hant", "Name_en", "Name_ja",
    "Description", "Description_zh-Hant", "Description_ja", "Description_en",
]
CARDPACK_TEXT_COMMENT = ["唯一标识", "备注", "名称", "", "", "", "描述", "描述", "説明", "Description"]

BUFF_DATA_HEADER = [
    "Id", "InitScript", "ApplyScript", "ClearScript", "ReducePerTurn",
    "ReducePerAttacked", "ReducePerUse", "UpperBound", "Icon", "Type",
    "Rarity", "Effects", "SoundEffects", "Action",
]
BUFF_DATA_COMMENT = [
    "唯一标识", "更新显示信息用的", "BUFF生效时的效果", "清除时效果", "层数每回合减少数",
    "层数每受击减少数", "层数每行动减少数", "层数上限", "图标路径", "类型",
    "稀有度", "特效", "", "",
]

BUFF_TEXT_HEADER = [
    "Id", "Note", "Name", "Name_zh-Hant", "Name_en", "Name_ja",
    "Description", "Description_zh-Hant", "Description_ja", "Description_en",
]
BUFF_TEXT_COMMENT = ["唯一标识", "备注", "名称", "名稱", "Name", "名称", "描述", "描述", "説明", "Description"]

