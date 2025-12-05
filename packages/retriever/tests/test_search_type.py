import asyncio
from enum import Enum

import aenum
from cognee.modules.search.types.SearchType import SearchType


async def search_type_is_enum_test():
    assert issubclass(SearchType, Enum)

    test_name = "TEST_ENUM_NAME"
    test_value = "Test_enum_value"

    aenum.extend_enum(SearchType, test_name, test_value)
    assert SearchType.TEST_ENUM_NAME in SearchType
    assert test_value in [st.value for st in SearchType]


async def main():
    await search_type_is_enum_test()


if __name__ == "__main__":
    asyncio.run(main())
