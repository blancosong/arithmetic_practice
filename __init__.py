# SPDX‑License‑Identifier: GPL‑3.0‑or‑later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

bl_info = {
    "name": "算术练习",
    "author": "User",
    "version": (1, 0, 0),
    "blender": (5, 2, 0),
    "location": "3D视图 → N面板 → %",
    "description": "算术练习，支持混合模式、单题型专项练习，记录每题耗时并生成本轮汇总报告",
    "category": "Utility",
}
import bpy
import random
import json
import time

SKILL_TYPES = [
    ("add_sub_near100", "凑整加减(99/101)"),
    ("mul_5_25_125", "×5/25/125 乘法"),
    ("div_5_25_125", "÷5/25/125 除法"),
    ("div_split", "拆分连除"),
    ("mul11_two", "两位数×11(×1.1)"),
    ("mul11_three", "三位数×11(×1.11)"),
    ("square_end5", "末位5平方"),
    ("mul_near_hundred", "近整百乘法98/103"),
    ("teen_mul_teen", "十几乘十几")
]
BASE_TYPES = [
    ("rand_add_sub", "随机大数加减"),
    ("rand_mul_div", "随机整数乘除"),
    ("rand_percent_mul", "整数×百分数"),
    ("rand_percent_div", "整数÷百分数")
]
ALL_TYPE_MAPPING = SKILL_TYPES + BASE_TYPES
MODE_ITEMS = [
    ("all_skill", "技巧混合", "仅各类速算技巧随机出题，不含基础四则、百分数"),
    ("all_calc_base", "全部混合", "巧算、四则、百分数全混合综合计算练习"),
    ("no_skill_only_base", "无技巧混合", "只出基础硬算与百分数，不包含任何速算巧算题型")
]
TYPE_NAME_MAP = {
    "add_sub_near100": "凑整加减(99/101)",
    "mul_5_25_125": "×5/25/125 乘法",
    "div_5_25_125": "÷5/25/125 除法",
    "div_split": "拆分连除",
    "mul11_two": "两位数×11(×1.1)",
    "mul11_three": "三位数×11(×1.11)",
    "square_end5": "末位5平方",
    "mul_near_hundred": "近整百乘法98/103",
    "teen_mul_teen": "十几乘十几",
    "rand_add_sub": "随机大数加减",
    "rand_mul_div": "随机整数乘除",
    "rand_percent_mul": "整数×百分数",
    "rand_percent_div": "整数÷百分数"
}

def is_valid_number_str(s: str) -> bool:
    if not s:
        return False
    s = s.strip()
    dot_count = 0
    for idx, ch in enumerate(s):
        if ch == '-':
            if idx != 0:
                return False
        elif ch == '.':
            dot_count +=1
            if dot_count>1:
                return False
        elif not ch.isdigit():
            return False
    return True

def elapsed_since(start_ts: float) -> float:
    """获取自时间戳以来经过秒数，兜底不出现负数"""
    return max(0.0, time.perf_counter() - start_ts)

def build_answer_record(question_text: str, tid: str, start_ts: float,
                        std_ans: float, user_show: str, status: str):
    """公共：构建单条答题记录字典，消除重复代码"""
    spend = elapsed_since(start_ts)
    return {
        "status": status,
        "spend": round(spend, 2),
        "type_name": TYPE_NAME_MAP.get(tid, "未知题型"),
        "question": question_text,
        "std_ans": std_ans,
        "user_ans_show": user_show
    }

def generate_question(context):
    sc = context.scene
    wm = context.window_manager
    wm.calc_q_start = time.perf_counter()

    mode = wm.calc_train_mode
    sel_skill = wm.calc_sel_skill
    sel_basic = wm.calc_sel_basic
    source = wm.calc_source_mode
    t = None
    if source == "special":
        if sel_skill != "none":
            t = sel_skill
        elif sel_basic != "none":
            t = sel_basic
    else:
        if mode == "all_skill":
            pool = [i[0] for i in SKILL_TYPES]
            t = random.choice(pool)
        elif mode == "all_calc_base":
            pool = [i[0] for i in ALL_TYPE_MAPPING]
            t = random.choice(pool)
        elif mode == "no_skill_only_base":
            pool = [i[0] for i in BASE_TYPES]
            t = random.choice(pool)
    q=""
    std=0.0
    explain=""
    if t == "add_sub_near100":
        a = random.randint(50,1500)
        b=random.choice([97,98,99,101,102,103,997,1002])
        if random.random()>0.5:
            q=f"{a} + {b} ="
            std=a+b
            off = b-100 if b>100 else 100-b
            explain=f"凑整速算：{a}+100={a+100}，{'再加' if b>100 else '再减'}{off}，结果{std}"
        else:
            big=a+b
            q=f"{big} - {b} ="
            std=big-b
            off=100-b if b<100 else b-100
            explain=f"减法凑整：先±100再修正差值{off}，结果{std}"
    elif t=="mul_5_25_125":
        mul=random.choice([5,25,125])
        num=random.randint(12,120)
        q=f"{num} × {mul} ="
        std=num*mul
        if mul==5:
            explain=f"×5 = ÷2×10 → {num/2}×10={std}"
        elif mul==25:
            explain=f"×25 = ÷4×100 → {num/4}×100={std}"
        else:
            explain=f"×125 = ÷8×1000 → {num/8}×1000={std}"
    elif t=="div_5_25_125":
        div=random.choice([5,25,125])
        num=random.choice([200,400,600,800,1000,1500,2000])
        q=f"{num} ÷ {div} ="
        std=num/div
        if div==5:
            explain=f"÷5 = ×2÷10 → {num*2}÷10={std}"
        elif div==25:
            explain=f"÷25 = ×4÷100 → {num*4}÷100={std}"
        else:
            explain=f"÷125 = ×8÷1000 → {num*8}÷1000={std}"
    elif t=="div_split":
        base=random.choice([12,15,16,18,20,24])
        total=random.randint(3,8)*base
        q=f"{total} ÷ {base} ="
        std=total/base
        d1=base/2
        d2=2
        explain=f"拆分连除简化：{total}÷{d1}÷{d2} 分步口算，结果{std}"
    elif t=="mul11_two":
        a=random.randint(12,98)
        q=f"{a} × 11 ="
        std=a*11
        s1,s2=int(str(a)[0]),int(str(a)[1])
        mid=s1+s2
        explain=f"两边一拉中间相加：{s1} ({s1}+{s2}={mid}) {s2}，结果{std}"
    elif t=="mul11_three":
        a=random.randint(100,500)
        q=f"{a} × 11 ="
        std=a*11
        explain="三位数×11：首尾拉开，相邻两位相加，满十进位"
    elif t=="square_end5":
        head=random.randint(1,12)
        num=head*10+5
        q=f"{num}² ="
        std=num*num
        p=head*(head+1)
        explain=f"十位×(十位+1)={p}，末尾补25，结果{std}"
    elif t=="mul_near_hundred":
        offset=random.randint(2,6)
        b=random.randint(20,80)
        if random.random()>0.5:
            a=100-offset
            q=f"{a} × {b} ="
            std=a*b
            explain=f"(100‑{offset})×{b}=100×{b}‑{offset}×{b}={std}"
        else:
            a=100+offset
            q=f"{a} × {b} ="
            std=a*b
            explain=f"(100+{offset})×{b}=100×{b}+{offset}×{b}={std}"
    elif t=="teen_mul_teen":
        a=random.randint(11,19)
        b=random.randint(11,19)
        q=f"{a} × {b} ="
        std=a*b
        ta=a-10
        tb=b-10
        explain=f"头×头=1，尾相加={ta+tb}，尾相乘={ta*tb}，合并进位{std}"
    elif t=="rand_add_sub":
        a=random.randint(100,9999)
        b=random.randint(100,9999)
        op=random.choice(["+","-"])
        if op=="+":
            q=f"{a} + {b} ="
            std=a+b
            explain="无专属速算技巧，纯硬算"
        else:
            q=f"{a} - {b} ="
            std=a-b
            explain="无专属速算技巧，纯硬算"
    elif t=="rand_mul_div":
        op=random.choice(["×","÷"])
        if op=="×":
            a=random.randint(12,99)
            b=random.randint(10,200)
            q=f"{a} × {b} ="
            std=a*b
            explain="无专属速算技巧，纯硬算"
        else:
            divisor=random.randint(2,40)
            ans=random.randint(10,300)
            num=divisor*ans
            q=f"{num} ÷ {divisor} ="
            std=num/divisor
            explain="无专属速算技巧，纯硬算"
    elif t=="rand_percent_mul":
        base=random.randint(800,9999)
        pct_list=[3,5,8,10,12.5,15,18,20,25,33.3,40,50,66.7,80]
        pct=random.choice(pct_list)
        q=f"{base} × {pct}% ="
        std=base*pct/100
        frac=100/pct
        explain=f"百化分：{pct}% = 1/{frac}，原式≈{base} ÷ {frac}，答案{std}"
    elif t=="rand_percent_div":
        base=random.randint(1000,9999)
        pct_list=[5,10,12.5,16.7,20,25,33.3,50,66.7]
        pct=random.choice(pct_list)
        q=f"{base} ÷ {pct}% ="
        std=base/(pct/100)
        mul_rate=100/pct
        explain=f"百化分转化：÷{pct}% = ×{mul_rate}，原式≈{base} × {mul_rate}，答案{std}"

    wm.calc_current_tid = t
    wm.calc_current_question = q
    wm.calc_answer_std = std
    wm.calc_explain_text = explain

def do_round_finish(context):
    sc = context.scene
    wm = context.window_manager
    user_input_raw = sc.user_answer_input.strip()
    std_val = wm.calc_answer_std
    q_text = wm.calc_current_question
    real_tid = wm.calc_current_tid
    round_total_sec = elapsed_since(wm.calc_round_start)

    status = "错误"
    user_show_str = "--"
    if user_input_raw != "" and is_valid_number_str(user_input_raw):
        user_val = float(user_input_raw)
        user_show_str = user_input_raw
        if abs(user_val - std_val) <= 0.01:
            status = "正确"

    rec = build_answer_record(
        question_text=q_text,
        tid=real_tid,
        start_ts=wm.calc_q_start,
        std_ans=std_val,
        user_show=user_show_str,
        status=status
    )

    lst = json.loads(wm.calc_round_json)
    lst.append(rec)
    wm.calc_round_json = json.dumps(lst)

    total_cnt = len(lst)
    correct_cnt = sum(1 for x in lst if x["status"]=="正确")
    accuracy = (correct_cnt/total_cnt*100.0) if total_cnt>0 else 0.0

    lines = ["本轮汇总"]
    lines.append(f"用时：{round_total_sec:.2f}s｜总题数：{total_cnt}题 ｜ 正确率：{accuracy:.2f}%")
    lines.append("")

    for idx, r in enumerate(lst,1):
        qq=r["question"]
        ss=r["status"]
        sp=r["spend"]
        tn=r["type_name"]
        us=r["user_ans_show"]
        std_raw = r["std_ans"]
        std_str = f"{std_raw:.2f}".rstrip("0").rstrip(".")
        mark = "✅" if ss == "正确" else "❌"
        line = f"{idx}｜{mark}｜{qq}{std_str}｜你的：{us}｜{sp:.2f}s｜{tn}"
        lines.append(line)

    wm.calc_report_text = "\n".join(lines)
    wm.calc_session_state = "READY"
    generate_question(context)
    sc.user_answer_input = ""

def _update_calc_source_mode(self, context):
    wm = context.window_manager
    val = wm.calc_source_mode
    if val == "global":
        wm.calc_train_mode = "all_calc_base"
        wm.calc_sel_skill = "none"
        wm.calc_sel_basic = "none"
        generate_question(context)
    else:
        wm.calc_sel_skill = "none"
        wm.calc_sel_basic = "none"
    context.scene.user_answer_input = ""

def _update_calc_train_mode(self, context):
    wm = context.window_manager
    generate_question(context)
    context.scene.user_answer_input = ""

class CALC_OT_SetSelSkill(bpy.types.Operator):
    bl_idname = "calc.set_sel_skill"
    bl_label = "选择速算技巧题型"
    bl_description = "选定一个速算技巧类的题型进行专项练习"
    bl_options = {'REGISTER', 'UNDO'}
    tid: bpy.props.StringProperty()
    def execute(self, context):
        wm = context.window_manager
        wm.calc_sel_skill = self.tid
        wm.calc_sel_basic = "none"
        generate_question(context)
        wm.fold_skill = False
        wm.fold_basic = False
        context.scene.user_answer_input = ""
        return {"FINISHED"}

class CALC_OT_SetSelBasic(bpy.types.Operator):
    bl_idname = "calc.set_sel_basic"
    bl_label = "选择基础硬算题型"
    bl_description = "选定一个基础硬算题型进行专项练习"
    bl_options = {'REGISTER', 'UNDO'}
    tid: bpy.props.StringProperty()
    def execute(self, context):
        wm = context.window_manager
        wm.calc_sel_basic = self.tid
        wm.calc_sel_skill = "none"
        generate_question(context)
        wm.fold_skill = False
        wm.fold_basic = False
        context.scene.user_answer_input = ""
        return {"FINISHED"}

class CALC_OT_ToggleFold(bpy.types.Operator):
    bl_idname = "calc.toggle_fold"
    bl_label = "折叠展开分组"
    bl_description = "折叠或展开题型选择分组列表"
    bl_options = {'REGISTER', 'UNDO'}
    fold_key: bpy.props.StringProperty()
    def execute(self, context):
        wm = context.window_manager
        if wm.calc_source_mode == "special":
            if self.fold_key == "fold_skill":
                if not wm.fold_skill:
                    wm.fold_skill = True
                    wm.fold_basic = False
                else:
                    wm.fold_skill = False
            elif self.fold_key == "fold_basic":
                if not wm.fold_basic:
                    wm.fold_basic = True
                    wm.fold_skill = False
                else:
                    wm.fold_basic = False
        else:
            if self.fold_key == "fold_skill":
                wm.fold_skill = not wm.fold_skill
            elif self.fold_key == "fold_basic":
                wm.fold_basic = not wm.fold_basic
        return {"FINISHED"}

class CALC_OT_ReadyStart(bpy.types.Operator):
    bl_idname = "calc.ready_start"
    bl_label = "▶ 开始"
    bl_description = "开启一轮练习会话，开始生成题目作答"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        wm = context.window_manager
        wm.calc_round_json = json.dumps([])
        wm.calc_report_text = ""
        wm.calc_session_state = "PLAY"
        wm.calc_round_start = time.perf_counter()
        wm.round_done_count = 0
        generate_question(context)
        context.scene.user_answer_input = ""
        return {"FINISHED"}

class CALC_OT_NextOne(bpy.types.Operator):
    bl_idname = "calc.next_one"
    bl_label = "下一题"
    bl_description = "保存当前答题记录，继续下一道题目"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        sc = context.scene
        wm = context.window_manager
        raw_in = sc.user_answer_input.strip()
        if not is_valid_number_str(raw_in):
            return {"CANCELLED"}

        std_val = wm.calc_answer_std
        q_text = wm.calc_current_question
        real_tid = wm.calc_current_tid
        user_val = float(raw_in)
        status = "正确" if abs(user_val - std_val) <=0.01 else "错误"

        rec = build_answer_record(
            question_text=q_text,
            tid=real_tid,
            start_ts=wm.calc_q_start,
            std_ans=std_val,
            user_show=raw_in,
            status=status
        )

        lst = json.loads(wm.calc_round_json)
        lst.append(rec)
        wm.calc_round_json = json.dumps(lst)

        wm.round_done_count += 1
        generate_question(context)
        sc.user_answer_input = ""
        return {"FINISHED"}

class CALC_OT_SubmitRound(bpy.types.Operator):
    bl_idname = "calc.submit_round"
    bl_label = "提交并结束本轮"
    bl_description = "提交当前答案，结束本轮练习，生成本轮汇总报告"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        do_round_finish(context)
        return {"FINISHED"}

class CALC_OT_NewQuestion(bpy.types.Operator):
    bl_idname = "calc.new_question"
    bl_label = "换一题"
    bl_description = "跳过当前题目，获取新的题目（单题型模式）"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        generate_question(context)
        context.scene.user_answer_input = ""
        return {"FINISHED"}

class CALC_OT_SubmitAnswer(bpy.types.Operator):
    bl_idname = "calc.submit_answer"
    bl_label = "提交答案"
    bl_description = "提交作答，弹窗提示对错（单题型模式）"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        sc = context.scene
        s = sc.user_answer_input.strip()
        if not is_valid_number_str(s):
            self.report({"WARNING"}, "请输入有效数字")
            return {"CANCELLED"}
        wm = context.window_manager
        std = wm.calc_answer_std
        user_ans = float(s)
        if abs(user_ans - std) <= 0.01:
            self.report({"INFO"}, f"答对！标准答案：{std}")
        else:
            self.report({"ERROR"}, f"答错！标准答案：{std}")
        generate_question(context)
        sc.user_answer_input = ""
        return {"FINISHED"}

class CALC_PT_Panel(bpy.types.Panel):
    bl_label = "🧮算术练习"
    bl_idname = "CALC_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "%"

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        wm = context.window_manager
        source = wm.calc_source_mode
        is_mix_mode = (source == "global")

        if not (is_mix_mode and wm.calc_session_state == "PLAY"):
            box_src = layout.box()
            box_src.label(text="模式选择")
            row_mode = box_src.row(align=True)
            row_mode.prop(wm, "calc_source_mode", expand=True)

            layout.separator()
            if source == "global":
                box_m = layout.box()
                box_m.label(text="混合题型")
                row_sub = box_m.row(align=True)
                row_sub.prop(wm, "calc_train_mode", expand=True)

            elif source == "special":
                box_sk = layout.box()
                row_f1 = box_sk.row(align=True)
                row_f1.operator("calc.toggle_fold",text="速算技巧").fold_key="fold_skill"
                if wm.fold_skill:
                    for tid,name in SKILL_TYPES:
                        box_sk.operator("calc.set_sel_skill",text=name).tid=tid
                box_bs = layout.box()
                row_f2 = box_bs.row(align=True)
                row_f2.operator("calc.toggle_fold",text="基础题型").fold_key="fold_basic"
                if wm.fold_basic:
                    for tid,name in BASE_TYPES:
                        box_bs.operator("calc.set_sel_basic",text=name).tid=tid
                if wm.calc_sel_skill == "none" and wm.calc_sel_basic == "none":
                    layout.label(text="提示：请点击上方选择具体题型开始出题")
                else:
                    cur_tid = wm.calc_sel_skill if wm.calc_sel_skill != "none" else wm.calc_sel_basic
                    for tid,name in ALL_TYPE_MAPPING:
                        if tid == cur_tid:
                            layout.label(text=f"【当前选中】：{name}")
                            break

        layout.separator()

        if is_mix_mode and wm.calc_session_state == "PLAY":
            col_play = layout.column()
            col_play.label(text=f"本轮第 {wm.round_done_count + 1} 题")
            row_eq = col_play.row(align=True)
            row_eq.label(text=wm.calc_current_question)
            row_eq.prop(sc,"user_answer_input",text="")

            row_btn = col_play.row(align=True)
            valid_input = is_valid_number_str(sc.user_answer_input.strip())
            row_btn.enabled = valid_input
            row_btn.operator("calc.next_one", text="下一题")

            row_btn2 = col_play.row(align=True)
            row_btn2.enabled = True
            row_btn2.operator("calc.submit_round", text="提交并结束本轮")

        elif is_mix_mode and wm.calc_session_state == "READY":
            layout.operator("calc.ready_start")
        else:
            if wm.calc_sel_skill != "none" or wm.calc_sel_basic != "none":
                row_eq = layout.row(align=True)
                row_eq.label(text=wm.calc_current_question)
                row_eq.prop(sc,"user_answer_input",text="")
                row_btn = layout.row()
                row_btn.operator("calc.new_question",text="换一题")
                row_btn.operator("calc.submit_answer",text="提交答案")

        layout.separator()
        box_report = layout.box()
        if is_mix_mode:
            if wm.calc_report_text:
                for line in wm.calc_report_text.splitlines():
                    box_report.label(text=line)
        else:
            if wm.calc_sel_skill != "none" or wm.calc_sel_basic != "none":
                box_report.label(text=f"解析：{wm.calc_explain_text}")

classes = [
    CALC_OT_SetSelSkill,
    CALC_OT_SetSelBasic,
    CALC_OT_ToggleFold,
    CALC_OT_ReadyStart,
    CALC_OT_NextOne,
    CALC_OT_SubmitRound,
    CALC_OT_NewQuestion,
    CALC_OT_SubmitAnswer,
    CALC_PT_Panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.user_answer_input = bpy.props.StringProperty(name="答案输入")
    wm = bpy.types.WindowManager

    wm.calc_source_mode = bpy.props.EnumProperty(
        items=[
            ("global", "混合模式", "混合模式，多题型随机出题"),
            ("special", "单题型模式", "固定单一题型反复训练")
        ],
        default="global",
        update=_update_calc_source_mode
    )
    wm.calc_train_mode = bpy.props.EnumProperty(
        items=MODE_ITEMS,
        default="all_calc_base",
        update=_update_calc_train_mode
    )

    wm.calc_sel_skill = bpy.props.StringProperty(default="none")
    wm.calc_sel_basic = bpy.props.StringProperty(default="none")
    wm.fold_skill = bpy.props.BoolProperty(default=False)
    wm.fold_basic = bpy.props.BoolProperty(default=False)

    wm.calc_session_state = bpy.props.StringProperty(default="READY")
    wm.calc_q_start = bpy.props.FloatProperty(default=0.0)
    wm.calc_round_start = bpy.props.FloatProperty(default=0.0)
    wm.calc_round_json = bpy.props.StringProperty(default="[]")
    wm.calc_report_text = bpy.props.StringProperty(default="")
    wm.calc_current_question = bpy.props.StringProperty(default="")
    wm.calc_answer_std = bpy.props.FloatProperty(default=0.0)
    wm.calc_explain_text = bpy.props.StringProperty(default="")
    wm.calc_current_tid = bpy.props.StringProperty(default="")
    wm.round_done_count = bpy.props.IntProperty(default=0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene,"user_answer_input"):
        del bpy.types.Scene.user_answer_input
    wm = bpy.types.WindowManager
    props = [
        "calc_source_mode","calc_train_mode","calc_sel_skill","calc_sel_basic",
        "fold_skill","fold_basic","calc_session_state","calc_q_start","calc_round_start",
        "calc_round_json","calc_report_text","calc_current_question","calc_answer_std",
        "calc_explain_text","calc_current_tid","round_done_count"
    ]
    for p in props:
        if hasattr(wm,p):
            delattr(wm,p)

if __name__ == "__main__":
    register()
