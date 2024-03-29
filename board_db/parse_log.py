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


def parse_summaries(filename):
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

def parse_voltages(filename):
    d = {}

    with open(filename, "r") as f:
        for line in f:
            line = line.lower()
            base_str = "Current reading for channel".lower()
            idx = line.find(base_str)
            if (idx != -1):
                pin = line[idx + len(base_str):line.find(":")].strip()
                voltage = line[line.find(":") + len(":"):line.find("a", line.find(":"))].strip()
                d[f"pin{pin}"] = voltage
    return d

def parse_log(filename):
	return map_keys({**parse_summaries(filename), **parse_voltages(filename)})

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

def map_keys(d):
    mapped_d = {}
    mapped_d["vme basic test-vme_summary"] = '1' if d["basic vme test"] else '0'
    mapped_d["fpga clock test-fpgaclk_summary"] = '1' if d["clock synthesizer communication"] else '0'
    mapped_d["sysmon test-sysmon_summary"] = '1' if d["voltage & current test"] else '0'
    mapped_d["ccb test-ccb_summary"] = '1' if d["ccb register"] else '0'
    mapped_d["otmb test-otmb_summary"] = '1' if d["otmb prbs"] else '0'
    mapped_d["lvmb test-lvmb_summary"] = '1' if d["lvmb"] else '0'
    mapped_d["dcfeb jtag test-dcfebjtag_summary"] = '1' if d["dcfeb jtag"] else '0'
    mapped_d["dcfeb fast signal test-dcfebfastsignal_summary"] = '1' if d["dcfeb pulses"] else '0'
    mapped_d["prom test-prom_summary"] = '1' if d["spi check"] else '0'
    # mapped_d["is_odmb7"] = d["odmb7"]
    for (k, v) in d.items():
        if "pin" in k:
            _, pin_idx = k.split("pin")
            mapped_d[f"sysmon test-sysmon_current{pin_idx}"] = v
    return mapped_d

#add_to_db(
#    "dummy.db",
#    ["sample_odmb5", "sample_odmb7"],
#    [parse_log("./output_odmb5.txt"), parse_log("./output_odmb7.txt")],
#)

#d = parse_log("output_odmb5.txt")
#print(d)
