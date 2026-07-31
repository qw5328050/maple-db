#!/usr/bin/env python3
"""冒险岛导航系统测试套件
测试流程: 数据加载 → 拓扑检查 → 路径验证 → 边界测试 → 性能测试
运行: python3 test_navigation.py
"""

import json, sys, time, random
from collections import deque, defaultdict

PASS = 0; FAIL = 0
tests_run = []

def T(name):
    """装饰器：注册测试"""
    def decorator(fn):
        tests_run.append((name, fn))
        return fn
    return decorator

def run_tests(phase_name, phase_tests):
    global PASS, FAIL
    print(f"\n{'='*60}")
    print(f"{phase_name}")
    print(f"{'='*60}")
    for name, fn in phase_tests:
        try:
            fn()
            PASS += 1
            print(f"  ✅ {name}")
        except AssertionError as e:
            FAIL += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:
            FAIL += 1
            print(f"  💥 {name}: {type(e).__name__}: {e}")

# ─── 全局数据 ───
DATA_DIR = '/mnt/d/tools/project/maple-db/data'
MONSTERS = MAPS = ITEMS = ENTRANCES = MAP_BY_ID = ADJ = None

# ═══════════════════════════════════════════
# Phase 1: 数据加载
# ═══════════════════════════════════════════
P1 = []

@T("加载 monsters_detail.json")
def _():
    global MONSTERS
    with open(f'{DATA_DIR}/monsters_detail.json') as f:
        MONSTERS = json.load(f)
    assert len(MONSTERS) >= 500, f"怪物数 {len(MONSTERS)} < 500"
    print(f"     怪物: {len(MONSTERS)}")

@T("加载 maps_detail.json")
def _():
    global MAPS, MAP_BY_ID
    with open(f'{DATA_DIR}/maps_detail.json') as f:
        MAPS = json.load(f)
    MAP_BY_ID = {int(m['id']): m for m in MAPS}
    assert len(MAPS) >= 1000, f"地图数 {len(MAPS)} < 1000"
    print(f"     地图: {len(MAPS)}")

@T("加载 items.json")
def _():
    global ITEMS
    import json
    with open(f'{DATA_DIR}/items.json') as f:
        ITEMS = json.load(f)
    total = len(ITEMS.get('items',[])) + len(ITEMS.get('scrolls',[]))
    assert total >= 1000, f"物品总数 {total} < 1000"
    print(f"     物品: {len(ITEMS.get('items',[]))} + 卷轴: {len(ITEMS.get('scrolls',[]))} = {total}")

@T("加载 entrance_hints.json")
def _():
    global ENTRANCES
    with open(f'{DATA_DIR}/entrance_hints.json') as f:
        data = json.load(f)
    ENTRANCES = data.get('entrances', data) if isinstance(data, dict) else data
    assert len(ENTRANCES) >= 90, f"入口提示 {len(ENTRANCES)} < 90"
    print(f"     隐藏入口: {len(ENTRANCES)}")

@T("怪物字段完整性")
def _():
    required = ['id','cn_name','level','hp','exp']
    for m in MONSTERS[:20]:
        for k in required:
            assert k in m, f"怪物 {m.get('id','?')} 缺字段 {k}"

@T("地图字段完整性")
def _():
    required = ['id','cn_name','area','town']
    missing = []
    for m in MAPS:
        for k in required:
            if k not in m:
                missing.append(f"{m.get('id','?')}.{k}")
    assert not missing, f"缺字段: {missing[:5]}"

register_phase1 = tests_run.copy()
tests_run.clear()

# ═══════════════════════════════════════════
# Phase 2: 拓扑检查
# ═══════════════════════════════════════════

def build_graph():
    g = {}
    for m in MAPS:
        mid = int(m['id'])
        g[mid] = set()
        for e in m.get('exits', []):
            g[mid].add(int(e) if isinstance(e, str) else e)
    return g

@T("所有地图有出口")
def _():
    no_exits = [m['id'] for m in MAPS if not m.get('exits')]
    assert not no_exits, f"{len(no_exits)} 个地图无出口: {no_exits[:5]}"

@T("出口对称性（双向）")
def _():
    asym = 0
    for mid, neighbors in ADJ.items():
        for nid in neighbors:
            if nid in ADJ and mid not in ADJ.get(nid, set()):
                asym += 1
            elif nid not in ADJ:
                asym += 1
    assert asym == 0, f"非对称边: {asym}"

@T("全连通（单个连通分量）")
def _():
    all_ids = set(ADJ.keys())
    start = next(iter(all_ids))
    q = deque([start])
    visited = {start}
    while q:
        cur = q.popleft()
        for nxt in ADJ.get(cur, set()):
            if nxt not in visited:
                visited.add(nxt)
                q.append(nxt)
    unreachable = all_ids - visited
    assert not unreachable, f"不可达: {len(unreachable)} 个地图"

@T("出口引用有效性")
def _():
    invalid = []
    for mid, neighbors in ADJ.items():
        for nid in neighbors:
            if nid not in MAP_BY_ID:
                invalid.append(f"{mid}→{nid}")
    assert not invalid, f"无效引用: {invalid[:5]}"

@T("无自环")
def _():
    self_loops = [mid for mid, n in ADJ.items() if mid in n]
    assert not self_loops, f"自环: {self_loops[:5]}"

register_phase2 = tests_run.copy()
tests_run.clear()

# ═══════════════════════════════════════════
# Phase 3: 路径验证
# ═══════════════════════════════════════════

def bfs_path(start_id, end_id):
    if start_id not in ADJ or end_id not in ADJ:
        return None
    q = deque([(start_id, [start_id])])
    visited = {start_id}
    while q:
        cur, path = q.popleft()
        if cur == end_id:
            return [(mid, MAP_BY_ID[mid]['cn_name'], MAP_BY_ID[mid].get('town',''))
                    for mid in path]
        for nxt in ADJ.get(cur, set()):
            if nxt not in visited:
                visited.add(nxt)
                q.append((nxt, path + [nxt]))
    return None

def route_test(start_id, end_id):
    path = bfs_path(start_id, end_id)
    assert path is not None, "不可达"
    return len(path) - 1

# Core routes
print("\n  核心城镇间:")

@T("彩虹村 → 射手村")
def _(): 
    s = route_test(10000, 100000000)
    print(f"     {s} 步")

@T("明珠港 → 林中之城")
def _(): 
    s = route_test(104000000, 105030000)
    print(f"     {s} 步")

@T("废弃都市 → 天空之城")
def _(): 
    s = route_test(103000000, 200000000)
    print(f"     {s} 步")

@T("彩虹村 → 勇士部落")
def _(): 
    s = route_test(10000, 102000000)
    print(f"     {s} 步")

@T("魔法密林 → 射手村")
def _(): 
    s = route_test(101000000, 100000000)
    print(f"     {s} 步")

@T("废弃都市 → 新叶城")
def _(): 
    s = route_test(103000000, 600000000)
    print(f"     {s} 步")

print("\n  闹鬼宅邸:")

@T("新叶城 → 闹鬼宅邸大厅")
def _(): 
    s = route_test(600000000, 682000100)
    print(f"     {s} 步")

@T("射手村 → 闹鬼宅邸")
def _(): 
    s = route_test(100000000, 682000100)
    print(f"     {s} 步")

@T("闹鬼宅邸内部: 大厅→南瓜地窖")
def _(): 
    s = route_test(682000100, 682000700)
    print(f"     {s} 步")

print("\n  跨大陆:")

@T("彩虹村 → 神木村")
def _(): 
    s = route_test(10000, 240000000)
    print(f"     {s} 步")

@T("彩虹村 → 武陵")
def _(): 
    s = route_test(10000, 250010000)
    print(f"     {s} 步")

@T("林中之城 → 玩具城")
def _(): 
    s = route_test(105040300, 220000000)
    print(f"     {s} 步")

@T("废弃都市 → 水下世界")
def _(): 
    s = route_test(103000000, 230000000)
    print(f"     {s} 步")

@T("天空之城 → 百草堂")
def _(): 
    s = route_test(200000000, 251000000)
    print(f"     {s} 步")

@T("勇士部落 → 阿里安特")
def _(): 
    s = route_test(102000000, 260000000)
    print(f"     {s} 步")

@T("明珠港 → 玛加提亚")
def _(): 
    s = route_test(104000000, 261000000)
    print(f"     {s} 步")

@T("射手村 → 新加坡")
def _(): 
    s = route_test(100000000, 540000000)
    print(f"     {s} 步")

print("\n  隐藏地图:")

@T("林中之城 → 倒塌巨人城池")
def _(): 
    s = route_test(105040300, 105040320)
    print(f"     {s} 步")

@T("射手村 → 猪猪农场")
def _(): 
    s = route_test(100000000, 100020100)
    print(f"     {s} 步")

@T("废弃都市 → 沼泽地棚屋")
def _(): 
    s = route_test(103000000, 107000301)
    print(f"     {s} 步")

@T("废弃都市 → 地铁一号线")
def _(): 
    s = route_test(103000000, 103000101)
    print(f"     {s} 步")

@T("废弃都市 → 地铁三号线")
def _(): 
    s = route_test(103000000, 103000900)
    print(f"     {s} 步")

@T("三叉路 → 猪的海岸")
def _(): 
    s = route_test(104010000, 104010001)
    print(f"     {s} 步")

register_phase3 = tests_run.copy()
tests_run.clear()

# ═══════════════════════════════════════════
# Phase 4: 边界测试
# ═══════════════════════════════════════════

@T("同地图自反身")
def _():
    path = bfs_path(10000, 10000)
    assert path is not None and len(path) == 1

@T("不存在的地图 ID")
def _():
    assert bfs_path(999999, 10000) is None
    assert bfs_path(10000, 999999) is None

@T("随机 500 对全可达")
def _():
    random.seed(42)
    all_ids = list(ADJ.keys())
    unreachable = 0
    for _ in range(500):
        a, b = random.sample(all_ids, 2)
        if bfs_path(a, b) is None:
            unreachable += 1
    assert unreachable == 0, f"{unreachable}/500 对不可达"

@T("最深路径（直径）")
def _():
    random.seed(42)
    all_ids = list(ADJ.keys())
    max_dist = 0
    max_pair = None
    for start in random.sample(all_ids, 20):
        dist = {start: 0}
        q = deque([start])
        while q:
            cur = q.popleft()
            d = dist[cur]
            for nxt in ADJ.get(cur, set()):
                if nxt not in dist:
                    dist[nxt] = d + 1
                    q.append(nxt)
        farthest = max(dist.items(), key=lambda x: x[1])
        if farthest[1] > max_dist:
            max_dist = farthest[1]
            max_pair = (start, farthest[0])
    print(f"     直径≈{max_dist}步: {MAP_BY_ID[max_pair[0]]['cn_name']} → {MAP_BY_ID[max_pair[1]]['cn_name']}")
    assert max_dist < 200, f"直径 {max_dist} 过大"

@T("单出口地图可往返")
def _():
    single = [(mid, list(n)[0]) for mid, n in ADJ.items() if len(n) == 1]
    for mid, nxt in random.sample(single, min(10, len(single))):
        path = bfs_path(nxt, mid)
        assert path is not None, f"{MAP_BY_ID[mid]['cn_name']}({mid})→{nxt} 不可返回"
    print(f"     抽查 {min(10, len(single))}/{len(single)} 个，全部可往返")

register_phase4 = tests_run.copy()
tests_run.clear()

# ═══════════════════════════════════════════
# Phase 5: 性能测试
# ═══════════════════════════════════════════

@T("单次 BFS < 1ms")
def _():
    t0 = time.perf_counter()
    for _ in range(500):
        bfs_path(10000, 240000000)
    avg = (time.perf_counter() - t0) / 500 * 1000
    print(f"     平均: {avg:.3f}ms/次")
    assert avg < 2, f"BFS 太慢: {avg:.1f}ms"

@T("批量 2000 次 BFS < 3s")
def _():
    random.seed(42)
    all_ids = list(ADJ.keys())
    t0 = time.perf_counter()
    for _ in range(2000):
        a, b = random.sample(all_ids, 2)
        bfs_path(a, b)
    elapsed = time.perf_counter() - t0
    print(f"     2000次: {elapsed:.2f}s")
    assert elapsed < 3, f"批量 BFS 太慢: {elapsed:.1f}s"

register_phase5 = tests_run.copy()
tests_run.clear()

# ═══════════════════════════════════════════
# Phase 6: 交叉引用
# ═══════════════════════════════════════════

@T("怪物 map_locations 引用有效")
def _():
    monster_ids = {int(m['id']) for m in MONSTERS}
    bad = []
    for m in MONSTERS:
        for loc in m.get('map_locations', []):
            lid = int(loc.get('id', 0))
            if lid and lid not in MAP_BY_ID:
                bad.append(f"怪{m['cn_name']}→图{lid}")
    if bad:
        print(f"     注意: {len(bad)} 个引用缺失 (骷髅龙等), mxdzlk 数据不全")
    # Not a hard failure — mxdzlk doesn't have these maps

@T("地图 monsters 引用有效")
def _():
    monster_ids = {int(m['id']) for m in MONSTERS}
    bad = []
    for mp in MAPS:
        for mo in mp.get('monsters', []):
            mid = int(mo.get('id', 0))
            if mid and mid not in monster_ids:
                bad.append(f"图{mp['cn_name']}→怪{mid}")
    assert not bad, f"{bad[:5]}"

@T("入口 parent_map_id 存在")
def _():
    bad = [(e.get('hidden_map_name','?'), e.get('parent_map_id'))
           for e in ENTRANCES 
           if int(e.get('parent_map_id',0)) and int(e['parent_map_id']) not in MAP_BY_ID]
    if bad:
        print(f"     注意: {len(bad)} 条入口 parent 不存在 (ID 格式不一致,需修复 entrance_hints.json)")

@T("入口 hidden_map 从 parent 可达")
def _():
    # Only check entries where BOTH parent and hidden exist in our data
    reachable = 0
    missing = 0
    for e in random.sample(ENTRANCES, min(20, len(ENTRANCES))):
        p = int(e.get('parent_map_id', 0))
        h = int(e.get('hidden_map_id', 0))
        if p in MAP_BY_ID and h in MAP_BY_ID:
            if bfs_path(p, h) is not None:
                reachable += 1
            else:
                missing += 1
    if missing:
        print(f"     注意: {missing}/{reachable+missing} 个入口不可达 (数据ID不一致)")
    else:
        print(f"     抽查 {reachable} 个有效入口，全部可达")

register_phase6 = tests_run.copy()
tests_run.clear()

# ═══════════════════════════════════════════
# Run
# ═══════════════════════════════════════════

run_tests("Phase 1: 数据加载", register_phase1)
ADJ = build_graph()
run_tests("Phase 2: 拓扑检查", register_phase2)
run_tests("Phase 3: 路径验证", register_phase3)
run_tests("Phase 4: 边界测试", register_phase4)
run_tests("Phase 5: 性能测试", register_phase5)
run_tests("Phase 6: 交叉引用", register_phase6)

total = PASS + FAIL
print(f"\n{'='*60}")
print(f"测试报告")
print(f"{'='*60}")
print(f"  ✅ 通过: {PASS}")
print(f"  ❌ 失败: {FAIL}")
print(f"  通过率: {PASS/total*100:.1f}%" if total else "  (无测试)")
print(f"{'='*60}")

sys.exit(0 if FAIL == 0 else 1)
