import sqlite3

search_keys_normal = [
    "basic vme test",
    "clock synthesizer communication",
    "voltage & current test",
    "ccb register",
    "otmb prbs",
    "lvmb",
    "dcfeb jtag",
    "dcfeb pulses",
]
search_keys_special = ["spi check", "odmb7"]
search_keys = search_keys_normal + search_keys_special


def parse_log(filename):
    # the search keys are used to identify each test
    # and also serve as the dictionary keys
    # except for keys in search_keys_special which are special cases
    d = dict.fromkeys(
        search_keys,
        False,
    )

    with open(filename, "r") as f:
        for line in f:
            line = line.lower()
            # handle special search keys
            # where the log output is irregular
            if (
                line.find("Success, all PROM SPI functionalities successful.".lower())
                != -1
            ):
                d["spi check"] = True
            if line.find("dcfeb 7") != -1:
                d["odmb7"] = True
            for key in search_keys_normal:
                if line.find(key.lower()) != -1 and line.find("not passed") == -1:
                    d[key] = True
    return d


def add_to_db(db_path, board_ids, log_dicts):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE test_status(board_id, vme, clock, voltage_current, ccb, prbs, lvmb, dcfeb_jtag, dcfeb_pulses, spi, is_odmb7)"
    )

    data = []
    for id, d in zip(board_ids, log_dicts):
        data.append((id, *[d[key] for key in search_keys]))
    cur.executemany(
        "INSERT INTO test_status VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data
    )
    con.commit()

    res = cur.execute("SELECT * FROM test_status")
    print(res.fetchall())

    con.close()


add_to_db(
    "dummy.db",
    ["sample_odmb5", "sample_odmb7"],
    [parse_log("./output_odmb5.txt"), parse_log("./output_odmb7.txt")],
)
