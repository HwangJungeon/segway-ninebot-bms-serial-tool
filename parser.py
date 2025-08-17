from typing import Dict, Any, List

def compute_checksum(packet: bytes) -> int:
    s = sum(packet[2:-2]) & 0xFFFF
    return (~s) & 0xFFFF

def split_words_le(data: bytes) -> List[int]:
    words = []
    for i in range(0, len(data) - (len(data) % 2), 2):
        words.append(data[i] | (data[i+1] << 8))
    return words

def parse_fw_version(word: int) -> str:
    # ABCD -> PCB=A, FW=B.C.D
    a = (word >> 12) & 0xF
    b = (word >> 8) & 0xF
    c = (word >> 4) & 0xF
    d = word & 0xF
    return f"{a}.{b}.{c}.{d}"

def to_int16(word: int) -> int:
    return word if word < 0x8000 else word - 0x10000

def parse_packet(hex_or_bytes) -> Dict[str, Any]:
    if isinstance(hex_or_bytes, str):
        b = bytes.fromhex(hex_or_bytes.replace(' ', ''))
    else:
        b = bytes(hex_or_bytes)

    if not (len(b) >= 9 and b[0] == 0x5A and b[1] == 0xA5):
        raise ValueError('Invalid packet header or too short')

    length = b[2]
    src = b[3]
    tgt = b[4]
    cmd = b[5]
    index = b[6]
    data = b[7:7+length]
    csum_bytes = b[7+length:7+length+2]
    got_csum = csum_bytes[0] | (csum_bytes[1] << 8)
    calc_csum = compute_checksum(b)

    ok = got_csum == calc_csum

    words = split_words_le(data)

    parsed: Dict[str, Any] = {
        'raw': b,
        'length': length,
        'src': src,
        'tgt': tgt,
        'cmd': cmd,
        'index': index,
        'data_bytes': data,
        'data_words': words,
        'checksum_ok': ok,
        'checksum_got': got_csum,
        'checksum_calc': calc_csum,
        'fields': {}
    }

    if cmd == 0x04:
        if index == 0x10:
            serial_bytes = data[0:14]
            serial = serial_bytes.decode('ascii', errors='replace')
            parsed['fields']['BAT_SN'] = serial
            if len(words) >= 8:
                parsed['fields']['BAT_FW_VER_raw'] = words[7]
                parsed['fields']['BAT_FW_VER'] = parse_fw_version(words[7])
            if len(words) >= 9:
                parsed['fields']['BAT_CAPACITY_mAh'] = words[8]
            if len(words) >= 10:
                parsed['fields']['BAT_TOTAL_CAPACITY_mAh'] = words[9]
            if len(words) >= 11:
                parsed['fields']['BAT_DESIGN_VOLT_x10mV'] = words[10]
                parsed['fields']['BAT_DESIGN_VOLT_V'] = words[10] * 0.01
            if len(words) >= 12:
                parsed['fields']['BAT_CYCLE_TIMES'] = words[11]
            if len(words) >= 13:
                parsed['fields']['BAT_CHARGE_TIMES'] = words[12]
            if len(words) >= 16:
                parsed['fields']['raw_tail_words'] = words[13:16]
        
        elif index == 0x20:
            pass

        elif index == 0x30:
            if len(words) >= 1:
                parsed['fields']['BAT_FUN_BOOLEAN'] = words[0]
            if len(words) >= 2:
                parsed['fields']['BAT_REMAINING_CAP_mAh'] = words[1]
            if len(words) >= 3:
                parsed['fields']['BAT_REMAINING_CAP_PERCENT'] = words[2]
            if len(words) >= 4:
                raw_current = to_int16(words[3])
                parsed['fields']['BAT_CURRENT_raw'] = raw_current
                parsed['fields']['BAT_CURRENT_A'] = raw_current * 0.01
            if len(words) >= 5:
                parsed['fields']['BAT_VOLTAGE_raw'] = words[4]
                parsed['fields']['BAT_VOLTAGE_V'] = words[4] * 0.01
            if len(words) >= 6:
                w = words[5]
                t1 = (w & 0xFF) - 20
                t2 = ((w >> 8) & 0xFF) - 20
                parsed['fields']['BAT_TEMP1_C'] = t1
                parsed['fields']['BAT_TEMP2_C'] = t2
            if len(words) >= 7:
                parsed['fields']['BAT_BALANCE_STATUS'] = words[6]
            if len(words) >= 8:
                parsed['fields']['BAT_ODIS_STATE'] = words[7]
            if len(words) >= 9:
                parsed['fields']['BAT_OCHG_STATE'] = words[8]
            if len(words) >= 10:
                parsed['fields']['BAT_CAP_COULO'] = words[9]
            if len(words) >= 11:
                parsed['fields']['BAT_CAP_VOL'] = words[10]
            if len(words) >= 12:
                parsed['fields']['BAT_HEALTHY_percent'] = words[11]
            if len(words) >= 16:
                parsed['fields']['reserved_3C_3F'] = words[12:16]

        elif index == 0x40:
            cells = {}
            for i in range(10):
                if i < len(words) and words[i] != 0xFFFF:
                    cells[f'cell_{i+1}'] = words[i] / 1000.0
            parsed['fields']['cells'] = cells

        elif index == 0x50:
            pass

    return parsed
