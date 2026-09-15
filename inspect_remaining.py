from database import get_all_airdrops

wanted = {8, 10, 34, 43, 46, 50, 79}

for row in get_all_airdrops():
    if row[0] in wanted:
        print("\n" + "=" * 100)
        print(f"ID: {row[0]}")
        print(f"NAME: {row[1]}")
        print(f"DESCRIPTION:\n{row[3]}")
