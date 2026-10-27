import struct


def read_dbf(path):
    b = open(path, "rb").read()
    if len(b) < 33:
        raise ValueError("file too short")
    nrec = struct.unpack("<I", b[4:8])[0]
    hlen, rlen = struct.unpack("<HH", b[8:12])
    if not (32 < hlen < len(b)) or rlen < 2:
        raise ValueError("not a valid dBASE header")
    fields, p = [], 32
    while p < hlen and b[p] != 0x0D:
        name = b[p:p + 11].split(b"\0")[0].decode("latin1")
        fields.append((name, chr(b[p + 11]), b[p + 16]))
        p += 32
    rows = []
    for i in range(nrec):
        rec = b[hlen + i * rlen: hlen + (i + 1) * rlen]
        if len(rec) < rlen:
            break
        o, row = 1, {}
        for name, typ, width in fields:
            row[name] = rec[o:o + width].decode("latin1").strip() if typ != "M" else ""
            o += width
        rows.append(row)
    return rows
