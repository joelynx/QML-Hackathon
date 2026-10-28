import boto3, json, datetime, sys
out = sys.argv[1]
s = boto3.Session(profile_name="qhack")
res = {}
for region, name in [("us-west-1", "Cepheus"), ("eu-north-1", "Garnet")]:
    c = s.client("braket", region_name=region)
    devs = c.search_devices(filters=[])["devices"]
    for d in devs:
        print(region, d["deviceArn"], d["deviceName"], d["deviceStatus"], d["deviceType"])
    m = [d for d in devs if name.lower() in d["deviceName"].lower() and d["deviceType"] == "QPU"]
    for d in m:
        t = datetime.datetime.now(datetime.timezone.utc).isoformat()
        r = c.get_device(deviceArn=d["deviceArn"])
        r.pop("ResponseMetadata", None)
        r["_fetched_utc"] = t
        r["_region"] = region
        tag = "rigetti" if "Cepheus" in d["deviceName"] else "iqm_garnet"
        with open(f"{out}/calibration_{tag}.json", "w") as f:
            json.dump(r, f, indent=1, default=str)
        print("saved", tag, d["deviceName"], t, len(r["deviceCapabilities"]))
