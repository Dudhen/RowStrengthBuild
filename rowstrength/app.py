import sys
import re
import json
import asyncio
from importlib import resources

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

# -------- Константы/настройки --------
DISTANCES = [500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000]
SHOW_DISTANCES = [500, 1000, 2000, 3000, 5000, 6000, 10000]  # 7 строк
REPS_TABLE = {
    1: 100, 2: 97, 3: 94, 4: 92, 5: 89, 6: 86, 7: 83, 8: 81, 9: 78, 10: 75,
    11: 73, 12: 71, 13: 70, 14: 68, 15: 67, 16: 65, 17: 64, 18: 63, 19: 61,
    20: 60, 21: 59, 22: 58, 23: 57, 24: 56, 25: 55, 26: 54, 27: 53, 28: 52,
    29: 51, 30: 50
}
WINDOW_SIZE = (1000, 750)

IS_IOS = (sys.platform == "ios")
F_HEAD = 22 if IS_IOS else 18
F_LABEL = 16 if IS_IOS else 14
F_INPUT = 16 if IS_IOS else 14
PAD_MAIN = 16 if IS_IOS else 14
INP_W = 200

CLR_HEADER_BG = "#D9CCFF"
CLR_TABLE_BG = "#EDE7FF"
CLR_BTN_BG = "#D9CCFF"
CLR_BTN_FG = "#2B1C7A"
CLR_ACCENT = "#6A5ACD"


def S_MAIN():  return Pack(direction=COLUMN, padding=PAD_MAIN, flex=1)


def S_ROW():   return Pack(direction=ROW, padding_bottom=6)  # ← оставляем как было (без flex)


def S_COL():   return Pack(direction=COLUMN)


def S_HEAD():  return Pack(font_size=F_HEAD, padding_bottom=6)


def S_LBL():   return Pack(font_size=F_LABEL, padding_right=8, flex=1)


def S_INP(w=None, is_lang=None):
    if is_lang:
        kw = dict(font_size=F_INPUT, padding_right=10)
        if w is not None:
            kw["width"] = w
        return Pack(**kw)
    return Pack(font_size=F_INPUT, padding_right=10, width=INP_W)

# UI: compact time row — узкие инпуты для селектов времени
def S_INP_NARROW(w):
    return Pack(font_size=F_INPUT, padding_right=6, width=w)


def S_BTN():   return Pack(padding_top=10, padding_bottom=10, padding_left=12, padding_right=12, flex=1)


# -------- Локализация --------
LANGS = ["en", "de", "fr", "es", "ru"]
LANG_LABEL = {"en": "English", "de": "Deutsch", "fr": "Français", "es": "Español", "ru": "Русский"}
T = {
    # сплэш теперь в 2 строки и по центру
    "splash": {l: " Dev by Dudhen:\n@arseny.dudhen" for l in LANGS},
    "title": {l: "RowStrength by Dudhen" for l in LANGS},
    "mode_erg": {"en": "Ergometer", "de": "Ergometer", "fr": "Ergomètre", "es": "Ergometrо", "ru": "Эргометр"},
    "mode_bar": {"en": "Barbell", "de": "Langhantel", "fr": "Barre", "es": "Barra", "ru": "Штанга"},
    "language": {"en": "Language", "de": "Sprache", "fr": "Langue", "es": "Idioma", "ru": "Язык"},
    "gender": {"en": "   Gender", "de": "   Geschlecht", "fr": "   Sexe", "es": "   Sexo", "ru": "   Пол"},
    "female": {"en": "Female", "de": "Weiblich", "fr": "Femme", "es": "Mujer", "ru": "Жен"},
    "male": {"en": "Male", "de": "Мännlich", "fr": "Homme", "es": "Hombre", "ru": "Муж"},
    "weight": {"en": "   Body weight (kg)", "de": "   Körpergewicht (kg)", "fr": "   Poids (kg)",
               "es": "   Peso corporal (kg)",
               "ru": "   Вес (кг)"},
    "distance": {"en": "   Distance", "de": "   Distanz", "fr": "   Distance", "es": "   Distancia",
                 "ru": "   Дистанция"},
    "minutes": {"en": "   Min", "de": "   Min", "fr": "   Min", "es": "   Min", "ru": "   Мин"},
    "seconds": {"en": "   Sec", "de": "   Sek", "fr": "   Sec", "es": "   Seg", "ru": "   Сек"},
    "centis": {"en": "   Tenths", "de": "   Zehntel", "fr": "   Dixièmes", "es": "   Décimas", "ru": "   Миллисекунды"},
    # UI: compact time row — новый локализованный заголовок
    "time_compact": {
        "en": "   Time\n   (min:sec.ms)",
        "de": "   Zeit\n   (Min:Sek.ms)",
        "fr": "   Temps\n   (min:s.ms)",
        "es": "   Tiempo\n   (min:s.ms)",
        "ru": "   Время\n   (мин:сек.мс)",
    },
    "exercise": {"en": "   Exercise", "de": "   Übung", "fr": "   Exercice", "es": "   Ejercicio",
                 "ru": "   Упражнение"},
    "bar_weight": {"en": "   Bar weight (kg)", "de": "   Hantelgewicht (kg)", "fr": "   Charge (kg)",
                   "es": "   Peso en barra (kg)",
                   "ru": "   Вес на штанге (кг)"},
    "reps": {"en": "   Reps", "de": "   Wdh.", "fr": "   Répétitions", "es": "   Reps", "ru": "   Повторы"},
    "calc": {"en": "Calculate", "de": "Berechnen", "fr": "Calculer", "es": "Calcular", "ru": "Рассчитать"},
    # Заголовки таблиц
    "erg_tbl1_title": {
        "en": "  Results across distances",
        "de": "  Ergebnisse über Distanzen",
        "fr": "  Résultats par distances",
        "es": "  Resultados por distancias",
        "ru": "  Результаты по дистанциям",
    },
    "erg_tbl2_title": {
        "en": "  Barbell equivalents (bodyweight {w} kg)",
        "de": " " if False else "  Hantel-Äquivalente \n  (Körpergewicht {w} kg)",
        "fr": "  Équivalents barre (poids du corps {w} kg)",
        "es": "  Equivalentes con barra \n  (peso corporal {w} kg)",
        "ru": "  Эквивалент в штанге с весом {w} кг",
    },
    "bar_tbl_title": {
        "en": "  One-rep max\n  and 2k ergometer equivalent",
        "de": "  1RM\n  und 2-km-Ergometer-Äquivalent",
        "fr": "  1 RM\n  et équivalent ergomètre 2 km",
        "es": "  1RM\n  y equivalente de ergómetro 2 km",
        "ru": "  Разовый максимум\n  и эквивалент на эргометре 2км",
    },
    # Табличные подписи
    "tbl_1rm": {"en": "1 rep max", "de": "1RM", "fr": "1 RM", "es": "1RM", "ru": "Разовый макс."},
    "tbl_2k": {"en": "2k ergometer", "de": "2 km Ergo", "fr": "Ergo 2 km", "es": "Ergo 2 km", "ru": "2км эргометр"},
    # Упражнения
    "ex_bench": {"en": "Bench press", "de": "Bankdrücken", "fr": "Développé couché", "es": "Press banca", "ru": "Жим"},
    "ex_squat": {"en": "Squat", "de": "Knieбеuge", "fr": "Squat", "es": "Sentadilla", "ru": "Присед"},
    "ex_deadlift": {"en": "Deadlift", "de": "Kreuzheben", "fr": "Soulevé de terre", "es": "Peso muerto",
                    "ru": "Становая тяга"},
    # Ошибки
    "err_title": {"en": "Notice", "de": "Hinweis", "fr": "Avis", "es": "Aviso", "ru": "Упс"},
    "err_weight": {"en": "Body weight must be between 40 and 140 kg.",
                   "de": "Körpergewicht muss zwischen 40 und 140 kg liegen.",
                   "fr": "Le poids doit être entre 40 et 140 kg.",
                   "es": "El peso corporal debe estar entre 40 et 140 кг.",
                   "ru": "Упс: вес тела должен быть от 40 до 140"},
    "err_reps": {"en": "Supported reps: 1..30.",
                 "de": "Unterstützte Wiederholungen: 1..30.",
                 "fr": "Répétitions prises en charge : 1..30.",
                 "es": "Repeticiones soportadas: 1..30.",
                 "ru": "Поддерживаются повторы: 1..30."},
    "err_bar_weight": {"en": "Bar weight must be between 1 and 700 kg.",
                       "de": "Hantelgewicht muss zwischen 1 und 700 kg liegen.",
                       "fr": "La charge doit être entre 1 et 700 kg.",
                       "es": "El peso en barra debe estar entre 1 et 700 кг.",
                       "ru": "Вес на штанге должен быть от 1 до 700"},
    "err_no_data": {"en": "No data for the selected distance/gender.",
                    "de": "Keine Daten für die gewählte Distanz/Geschlecht.",
                    "fr": "Pas de données pour cette distance/genre.",
                    "es": "No hay datos para esta distancia/sexo.",
                    "ru": "Нет данных по выбранной дистанции и полу."},
    "err_time_range": {"en": "Time is out of range.", "de": "Zeit außerhalb des Bereichs.",
                       "fr": "Temps hors plage.", "es": "Tiempo fuera de rango.", "ru": "Время вне диапазона."},
    "err_no_strength": {"en": "No strength data for this body weight.",
                        "de": "Keine Kraftdaten für dieses Körpergewicht.",
                        "fr": "Pas de données de force pour ce poids.",
                        "es": "No hay datos de fuerza para este peso.",
                        "ru": "Нет силовых данных для указанного веса."},
    "err_1rm_map": {"en": "Unable to estimate 1RM percent for these inputs.",
                    "de": "Prozentsatz zum 1RM konnte nicht ermittelt werden.",
                    "fr": "Impossible d'estimer le pourcentage de 1RM.",
                    "es": "No se puede estimar el porcentaje de 1RM.",
                    "ru": "Не удалось сопоставить процент к 1ПМ для этих данных."},
}
EX_UI_TO_KEY = {
    lang: {
        T["ex_bench"][lang]: "bench-press",
        T["ex_squat"][lang]: "squat",
        T["ex_deadlift"][lang]: "deadlift",
    } for lang in LANGS
}
EX_KEY_TO_LABEL = {lang: {v: k for k, v in EX_UI_TO_KEY[lang].items()} for lang in LANGS}
GENDER_LABELS = {lang: [T["female"][lang], T["male"][lang]] for lang in LANGS}
GENDER_MAP = {lang: {GENDER_LABELS[lang][0]: "female", GENDER_LABELS[lang][1]: "male"} for lang in LANGS}


# -------- Утилиты расчёта/таблиц --------
def _two(n: int) -> str:
    return f"{n:02d}"


def get_split_500m(distance_m: int, time_mmss: str) -> str:
    m = re.fullmatch(r'\s*(\d{1,2}):(\d{2})\s*', time_mmss)
    mm, ss = int(m.group(1)), int(m.group(2))
    total_sec = mm * 60 + ss
    tenths_total = round(total_sec * 10 / (distance_m / 500))
    mins = tenths_total // 600
    sec_tenths = tenths_total % 600
    secs = sec_tenths // 10
    tenth = sec_tenths % 10
    return f"{mins:02d}:{secs:02d}.{tenth}/500m"


def load_json_from_package(filename: str):
    pkg = __package__ or "rowstrength"
    with resources.files(pkg).joinpath("data").joinpath(filename).open("r", encoding="utf-8") as f:
        return json.load(f)


def get_distance_data(gender, distance, data):
    return data.get(gender, {}).get(str(distance), {})


def get_strength_data(gender, bw, data):
    return data.get(gender, {}).get(str(int(bw)), {})


def parse_available_times(distance_data):
    mins = {}
    for key in distance_data.keys():
        m = re.fullmatch(r'\s*(\d{1,2}):(\d{2})\s*', key)
        if not m:
            continue
        mm, ss = _two(int(m.group(1))), _two(int(m.group(2)))
        mins.setdefault(mm, set()).add(ss)
    minutes_sorted = sorted(mins.keys(), key=lambda x: int(x))
    seconds_for_minute = {mm: sorted(list(sset), key=lambda x: int(x)) for mm, sset in mins.items()}
    return minutes_sorted, seconds_for_minute


def meters_from_key(k) -> int:
    m = re.search(r"\d+", str(k))
    return int(m.group()) if m else 0


def make_table(rows, col_flex=None):
    if not rows:
        return toga.Box(style=S_COL())
    cols = max(len(r) for r in rows)
    col_flex = col_flex or [1] * cols
    table = toga.Box(style=S_COL())
    for r in rows:
        row = toga.Box(style=Pack(direction=ROW, background_color=CLR_TABLE_BG, padding=6))
        for i in range(cols):
            text = r[i] if i < len(r) else ""
            lbl = toga.Label(text, style=Pack(flex=col_flex[i], font_size=F_INPUT))
            row.add(lbl)
        table.add(row)
    return table


# --- вспомогательный форс лэйаута для iOS ---
def _force_layout_ios(window):
    if sys.platform != "ios":
        return
    try:
        native = window._impl.native
        native.view.setNeedsLayout()
        native.view.layoutIfNeeded()
    except Exception:
        pass


# -------- Приложение --------
class RowStrengthApp(toga.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Язык по умолчанию — English
        self.lang = "en"
        self._updating = False
        self._erg_init_done = False
        self.rowing_data = None
        self.strength_data_all = None
        # ссылки на заголовки таблиц (создаются только при расчёте)
        self.erg_tbl1_title_label = None
        self.erg_tbl2_title_label = None
        self.bar_tbl_title_label = None
        # держим ссылки на страницы/колонки/табы
        self.erg_page = None
        self.erg_col = None
        self.bar_page = None
        self.bar_col = None
        self.tabs = None
        # Виджеты хедера
        self.header_dev_label = None
        self.header_lang_label = None
        self.lang_sel = None

        # --- Авторитетные значения времени (обход бага iOS Selection.value) ---
        self._min_value = "06"
        self._sec_value = "00"
        self._cen_value = "0"

        # Фикс «первого захода» на Штангу / после смены языка
        self._bar_needs_first_fix = True

    # ===== Сервис: безопасная установка items с сохранением value =====
    def _set_selection_items_preserve(self, selection: toga.Selection, items, desired_value):
        try:
            items_list = [str(x) for x in (list(items) if items is not None else [])]
            desired = None if desired_value is None else str(desired_value)
            selection.items = items_list

            if desired is None:
                return

            if desired in items_list:
                selection.value = desired
            else:
                combined = [desired] + [x for x in items_list if x != desired]
                selection.items = combined
                selection.value = desired
        except Exception:
            try:
                if desired_value is not None:
                    selection.value = str(desired_value)
            except Exception:
                pass

    # ========== iOS: принудительно задаём типы цифровой клавиатуры ==========
    def _apply_ios_keyboard_types(self):
        if not IS_IOS:
            return

        def _set_kb(widget, kb_code: int):
            try:
                native = widget._impl.native  # UITextField
                if native is None:
                    return
                native.keyboardType = kb_code
                native.reloadInputViews()
            except Exception:
                pass

        try:
            _set_kb(self.weight, 8)  # DecimalPad
            _set_kb(self.weight_b, 8)  # DecimalPad
            _set_kb(self.bar_weight, 8)  # DecimalPad
            _set_kb(self.reps, 4)  # NumberPad
        except Exception:
            pass

    # ========== iOS: синхронизация отображаемого текста Selection ==========
    def _ios_sync_selection_display(self, selection_widget: toga.Selection, index: int | None = None):
        if sys.platform != "ios":
            return
        try:
            items = list(selection_widget.items) or []
            if not items:
                return
            if index is None:
                vals = [row.value for row in items]
                cur = getattr(selection_widget, "value", None)
                index = vals.index(cur) if cur in vals else 0
            target = items[index].value
            try:
                selection_widget.value = target
            except Exception:
                pass
            try:
                native = selection_widget._impl.native  # UITextField
                if native:
                    try:
                        native.text = str(target)
                    except Exception:
                        pass
                    try:
                        picker = native.inputView
                    except Exception:
                        picker = None
                    if picker:
                        try:
                            picker.reloadAllComponents()
                        except Exception:
                            pass
                        try:
                            picker.selectRow_inComponent_animated(index, 0, False)
                        except Exception:
                            try:
                                picker.selectRow(index, inComponent=0, animated=False)
                            except Exception:
                                pass
                    try:
                        native.setNeedsLayout()
                        native.layoutIfNeeded()
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                selection_widget.refresh()
            except Exception:
                pass
            _force_layout_ios(self.main_window)
        except Exception:
            pass

    # ---- Сплэш ----
    def startup(self):
        self.main_window = toga.MainWindow(title="", size=WINDOW_SIZE)
        for attr in ("resizeable", "resizable"):
            try:
                setattr(self.main_window, attr, False)
                break
            except Exception:
                pass

        # Сплэш по центру, 2 строки
        splash = toga.Label(T["splash"][self.lang], style=Pack(font_size=18, text_align="center", color=CLR_ACCENT))
        center_row = toga.Box(style=Pack(direction=ROW, flex=1))
        center_row.add(toga.Box(style=Pack(flex=1)))
        center_row.add(splash)
        center_row.add(toga.Box(style=Pack(flex=1)))
        splash_root = toga.Box(children=[toga.Box(style=Pack(flex=1)), center_row, toga.Box(style=Pack(flex=1))],
                               style=Pack(direction=COLUMN, flex=1, padding=24))
        self.main_window.content = splash_root
        self.main_window.show()

        # Через 3 секунды строим и показываем готовый UI
        asyncio.get_event_loop().call_later(3.0, self._safe_build_main)

    def _safe_build_main(self):
        try:
            self._build_main()
        except Exception as e:
            self._info(str(e))

    def _info(self, msg: str):
        try:
            self.main_window.info_dialog(T["err_title"][self.lang], msg)
        except Exception:
            print(msg)

    def _dismiss_ios_inputs(self):
        if sys.platform != "ios":
            return
        try:
            from rubicon.objc import ObjCClass
            UIApplication = ObjCClass("UIApplication")
            app = UIApplication.sharedApplication
            key_window = app.keyWindow or (app.windows and app.windows.firstObject)
            if key_window:
                key_window.endEditing(True)
        except Exception:
            pass

    # ---- глубокий refresh поддерева ----
    def _deep_refresh(self, widget):
        try:
            widget.refresh()
        except Exception:
            pass
        content = getattr(widget, "content", None)
        if content is not None:
            self._deep_refresh(content)
        children = getattr(widget, "children", None)
        if children:
            for ch in list(children):
                self._deep_refresh(ch)

    # ---- «мягкий нудж» для обоих ScrollContainer ----
    def _nudge_scrollcontainers(self):
        for page in (self.erg_page, self.bar_page):
            if page is None:
                continue
            try:
                old = page.content
                dummy = toga.Box(style=Pack())  # временный контейнер
                page.content = dummy
                page.content = old
            except Exception:
                pass
            try:
                page.refresh()
            except Exception:
                pass
        try:
            self._deep_refresh(self.main_window.content)
            _force_layout_ios(self.main_window)
        except Exception:
            pass

    # ---- «сильный» нудж конкретного ScrollContainer (iOS) ----
    def _ios_strong_nudge_scrollcontainer(self, sc: toga.ScrollContainer | None):
        if sys.platform != "ios" or sc is None:
            return
        try:
            old = sc.content
            dummy = toga.Box(style=Pack())
            sc.content = dummy
            sc.content = old
        except Exception:
            pass
        try:
            native = sc._impl.native
            if native is not None:
                try:
                    native.setNeedsLayout()
                    native.layoutIfNeeded()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            sc.refresh()
        except Exception:
            pass
        try:
            self._deep_refresh(self.main_window.content)
            _force_layout_ios(self.main_window)
        except Exception:
            pass

    # ---- удалить ВСЕ «висячие» blur-вью (кроме navbar/tabbar) ----
    def _ios_strip_global_blurs(self):
        if sys.platform != "ios":
            return
        try:
            from rubicon.objc import ObjCClass
            UIVisualEffectView = ObjCClass("UIVisualEffectView")
            UINavigationBar = ObjCClass("UINavigationBar")
            UITabBar = ObjCClass("UITabBar")

            native_win = self.main_window._impl.native
            root = getattr(native_win, "view", None)
            if root is None:
                return

            def _keep(view):
                try:
                    parent = view.superview
                    while parent is not None:
                        if parent.isKindOfClass_(UINavigationBar) or parent.isKindOfClass_(UITabBar):
                            return True
                        parent = parent.superview if hasattr(parent, "superview") else None
                except Exception:
                    pass
                return False

            def _walk(v):
                try:
                    subs = list(v.subviews)
                except Exception:
                    subs = []
                for sv in subs:
                    try:
                        if sv.isKindOfClass_(UIVisualEffectView) and not _keep(sv):
                            sv.removeFromSuperview()
                            continue
                    except Exception:
                        pass
                    _walk(sv)

            _walk(root)
        except Exception:
            pass

    # ---- полная безопасная пересборка ScrollContainer «Штанги» (iOS) ----
    def _ios_recreate_bar_page(self):
        if not IS_IOS or self.bar_col is None or self.tabs is None:
            return
        try:
            new_sc = toga.ScrollContainer(content=self.bar_col, horizontal=False, style=Pack(flex=1))
            self.bar_page = new_sc
            try:
                items = list(self.tabs.content)
                try:
                    items[1].content = new_sc
                except Exception:
                    try:
                        self.tabs.content = [(T["mode_erg"][self.lang], self.erg_page),
                                             (T["mode_bar"][self.lang], new_sc)]
                    except Exception:
                        self.tabs.content = [(self.erg_page, T["mode_erg"][self.lang]),
                                             (new_sc, T["mode_bar"][self.lang])]
            except Exception:
                pass
        except Exception:
            pass

    # FIX(iOS layout): «тёплое» переключение на вкладку «Штанга» и обратно
    def _ios_warm_select_bar(self):
        if not IS_IOS or self.tabs is None:
            return
        try:
            initial = getattr(self.tabs, "current_tab", None)
        except Exception:
            initial = None

        switched = False
        # Пытаемся через current_tab разными способами
        try:
            self.tabs.current_tab = self.bar_page
            switched = True
        except Exception:
            try:
                self.tabs.current_tab = self.bar_col
                switched = True
            except Exception:
                try:
                    # Попробуем через OptionItem
                    items = list(self.tabs.content)
                    bar_item = None
                    erg_item = None
                    for it in items:
                        if getattr(it, "content", None) is self.bar_page or getattr(it, "content",
                                                                                    None) is self.bar_col:
                            bar_item = it
                        if getattr(it, "content", None) is self.erg_page or getattr(it, "content",
                                                                                    None) is self.erg_col:
                            erg_item = it
                    if bar_item is not None:
                        self.tabs.current_tab = bar_item
                        switched = True
                except Exception:
                    pass

        _force_layout_ios(self.main_window)
        self._nudge_scrollcontainers()

        # Возврат на исходный таб
        if switched:
            try:
                if initial is not None:
                    self.tabs.current_tab = initial
            except Exception:
                pass
        else:
            # Фоллбек: временно меняем порядок content и возвращаем
            try:
                self.tabs.content = [(T["mode_bar"][self.lang], self.bar_page),
                                     (T["mode_erg"][self.lang], self.erg_page)]
                _force_layout_ios(self.main_window)
                self._nudge_scrollcontainers()
                self.tabs.content = [(T["mode_erg"][self.lang], self.erg_page),
                                     (T["mode_bar"][self.lang], self.bar_page)]
            except Exception:
                try:
                    self.tabs.content = [(self.bar_page, T["mode_bar"][self.lang]),
                                         (self.erg_page, T["mode_erg"][self.lang])]
                    _force_layout_ios(self.main_window)
                    self._nudge_scrollcontainers()
                    self.tabs.content = [(self.erg_page, T["mode_erg"][self.lang]),
                                         (self.bar_page, T["mode_bar"][self.lang])]
                except Exception:
                    pass
        _force_layout_ios(self.main_window)

    # FIX(iOS layout): «фальш-пересчёт» в контейнере результатов «Штанги»
    def _ios_fake_recalc_bar(self):
        if not IS_IOS or self.bar_results_holder is None:
            return
        try:
            temp_title = toga.Label(" ")
            temp_tbl = make_table([[""]])
            # Временно наполняем holder
            self.bar_results_holder.add(toga.Box(children=[temp_title], style=S_ROW()))
            self.bar_results_holder.add(temp_tbl)
        except Exception:
            pass

        try:
            self.bar_results_holder.refresh()
        except Exception:
            pass
        try:
            self._deep_refresh(self.bar_col)
        except Exception:
            pass
        _force_layout_ios(self.main_window)

        # Удаляем временный контент без следов
        try:
            self._really_clear_holder_children(self.bar_results_holder)
        except Exception:
            pass
        try:
            self.bar_results_holder.refresh()
        except Exception:
            pass
        _force_layout_ios(self.main_window)

    # ---- гарантированная «инициализация» лэйаута Штанги (один раз) ----
    def _ensure_bar_ready_once(self):
        if not IS_IOS:
            return
        # Выполняем только при первом заходе или после смены языка
        if not self._bar_needs_first_fix:
            return
        self._bar_needs_first_fix = False

        # Последовательность: пересоздать скролл → нуджи → убрать возможные блюры
        self._ios_recreate_bar_page()
        self._ios_strong_nudge_scrollcontainer(self.bar_page)
        self._nudge_scrollcontainers()
        self._ios_strip_global_blurs()

        # FIX(iOS layout): тёплый выбор вкладки и фальш-пересчёт (пока вкладка скрыта)
        self._ios_warm_select_bar()
        self._ios_fake_recalc_bar()

        # И ещё пара проходов с маленькой задержкой — чтобы поймать поздние перерисовки
        loop = asyncio.get_event_loop()
        loop.call_later(0.02, lambda: (self._ios_strong_nudge_scrollcontainer(self.bar_page),
                                       self._nudge_scrollcontainers()))
        loop.call_later(0.03, lambda: (self._ios_warm_select_bar(),))  # FIX(iOS layout): повтор warm-select
        loop.call_later(0.06, lambda: (self._ios_fake_recalc_bar(),))  # FIX(iOS layout): повтор fake-recalc
        loop.call_later(0.08, lambda: (self._ios_strip_global_blurs(),
                                       self._ios_strong_nudge_scrollcontainer(self.bar_page)))
        loop.call_later(0.15, lambda: (_force_layout_ios(self.main_window),))

    # ---- надёжная очистка контейнера результатов ----
    def _really_clear_holder_children(self, holder: toga.Box | None):
        if holder is None:
            return
        try:
            for ch in list(getattr(holder, "children", []) or []):
                try:
                    holder.remove(ch)
                except Exception:
                    pass
            try:
                holder.children.clear()
            except Exception:
                try:
                    holder.children = []
                except Exception:
                    pass
            holder.refresh()
        except Exception:
            pass

    def _clear_results_holder(self, which: str):
        if which == "erg":
            self._really_clear_holder_children(getattr(self, "erg_results_holder", None))
            self.erg_tbl1_title_label = None
            self.erg_tbl2_title_label = None
        else:
            self._really_clear_holder_children(getattr(self, "bar_results_holder", None))
            self.bar_tbl_title_label = None
        try:
            self._deep_refresh(self.main_window.content)
            _force_layout_ios(self.main_window)
        except Exception:
            pass

    def _clear_all_results(self):
        self._clear_results_holder("erg")
        self._clear_results_holder("bar")

    # ---- Основной UI ----
    def _build_main(self):
        # 1) Загружаем данные
        self.rowing_data = load_json_from_package("data_for_rowing_app.json")
        self.strength_data_all = load_json_from_package("data_for_strength_app.json")

        # 2) Предварительные списки минут/секунд и стартовые значения
        try:
            g_key_default = "male"
            dist_default = 2000
            dist_data_default = get_distance_data(g_key_default, dist_default, self.rowing_data)
            if dist_data_default:
                minutes_list, sec_map = parse_available_times(dist_data_default)
                min_default = minutes_list[1] if len(minutes_list) >= 2 else minutes_list[0]
                sec_items_for_min = sec_map.get(min_default, ["00"])
                sec_default = sec_items_for_min[0] if sec_items_for_min else "00"
            else:
                minutes_list = ["06"]; sec_items_for_min = ["00"]; min_default, sec_default = "06", "00"
        except Exception:
            minutes_list = ["06"]; sec_items_for_min = ["00"]; min_default, sec_default = "06", "00"

        self._min_value = min_default
        self._sec_value = sec_default
        self._cen_value = "0"

        # ====== Верхний фиолетовый прямоугольник (шапка) ======
        self.header_dev_label = toga.Label(
            "RowStrength by Dudhen",
            style=Pack(font_size=F_HEAD, color="#501c59", text_align="center", padding_top=8, padding_bottom=4)
        )
        top_row = toga.Box(style=Pack(direction=ROW, padding_top=6, padding_bottom=4, background_color=CLR_HEADER_BG))
        top_row.add(toga.Box(style=Pack(flex=1)))
        top_row.add(self.header_dev_label)
        top_row.add(toga.Box(style=Pack(flex=1)))

        # Строка 2: язык справа
        self.lang_sel = toga.Selection(
            items=[LANG_LABEL[c] for c in LANGS],
            value=LANG_LABEL[self.lang],
            on_change=self._on_lang_change,
            style=S_INP(is_lang=True)
        )
        self.header_lang_label = toga.Label(
            T["language"][self.lang],
            style=Pack(font_size=F_LABEL, padding_left=8, padding_right=6)
        )
        lang_row = toga.Box(style=Pack(direction=ROW, padding_top=2, padding_bottom=6, background_color=CLR_HEADER_BG))
        lang_row.add(toga.Box(style=Pack(flex=1)))
        lang_row.add(self.header_lang_label)
        lang_row.add(self.lang_sel)

        header = toga.Box(
            style=Pack(
                direction=COLUMN,
                background_color=CLR_HEADER_BG,
                padding_left=0,
                padding_right=0,
                padding_top=8,
                padding_bottom=10
            )
        )
        header.add(top_row)
        header.add(lang_row)

        # ===== Вкладка Эргометр =====
        self.gender_lbl = toga.Label(T["gender"][self.lang], style=S_LBL())
        self.gender = toga.Selection(items=GENDER_LABELS[self.lang], value=GENDER_LABELS[self.lang][1],
                                     on_change=self._on_gender_change, style=S_INP(160))
        self.weight_lbl = toga.Label(T["weight"][self.lang], style=S_LBL())
        self.weight = toga.NumberInput(step=1, value=80, style=S_INP(160))

        self.distance_lbl = toga.Label(T["distance"][self.lang], style=S_LBL())
        self.distance = toga.Selection(items=[str(d) for d in DISTANCES], value="2000",
                                       on_change=self._on_distance_change, style=S_INP(160))

        # UI: compact time row — один заголовок «Время (мин:сек.мс)» вместо трёх
        self.time_lbl = toga.Label(T["time_compact"][self.lang], style=S_LBL())

        # Селекты времени (узкие) + разделители ":" и "."
        self.min_sel = toga.Selection(items=minutes_list, value=min_default,
                                      on_change=self._on_minute_change, style=S_INP_NARROW(48))  # UI: compact time row
        self.sec_sel = toga.Selection(items=list(sec_items_for_min), value=sec_default,
                                      on_change=self._on_second_change, style=S_INP_NARROW(48))  # UI: compact time row
        self.cen_sel = toga.Selection(items=[str(i) for i in range(10)], value="0",
                                      on_change=self._on_centi_change, style=S_INP_NARROW(48))  # UI: compact time row
        sep_style = Pack(padding_left=4, padding_right=4, font_size=F_INPUT)  # UI: compact time row
        time_inputs = toga.Box(style=Pack(direction=ROW))  # UI: compact time row
        time_inputs.add(self.min_sel)
        time_inputs.add(toga.Label(":", style=sep_style))
        time_inputs.add(self.sec_sel)
        time_inputs.add(toga.Label(".", style=sep_style))
        time_inputs.add(self.cen_sel)

        self.btn_erg = toga.Button(T["calc"][self.lang], on_press=self.calculate_erg, style=S_BTN())
        try:
            self.btn_erg.style.background_color = CLR_BTN_BG
            self.btn_erg.style.color = CLR_BTN_FG
        except Exception:
            pass

        self.erg_results_holder = toga.Box(style=S_COL())

        erg_rows = [
            toga.Box(children=[self.gender_lbl, self.gender], style=S_ROW()),
            toga.Box(children=[self.weight_lbl, self.weight], style=S_ROW()),
            toga.Box(children=[self.distance_lbl, self.distance], style=S_ROW()),
            toga.Box(children=[self.time_lbl, time_inputs], style=S_ROW()),  # UI: compact time row
            toga.Box(children=[self.btn_erg], style=S_ROW()),
            self.erg_results_holder,
        ]
        self.erg_col = toga.Box(children=erg_rows, style=Pack(direction=COLUMN, flex=1))
        self.erg_page = toga.ScrollContainer(content=self.erg_col, horizontal=False, style=Pack(flex=1))

        # ===== Вкладка Штанга =====
        self.gender_b_lbl = toga.Label(T["gender"][self.lang], style=S_LBL())
        self.gender_b = toga.Selection(items=GENDER_LABELS[self.lang], value=GENDER_LABELS[self.lang][1],
                                       style=S_INP(160))
        self.weight_b_lbl = toga.Label(T["weight"][self.lang], style=S_LBL())
        self.weight_b = toga.NumberInput(step=1, value=80, style=S_INP(160))

        self.ex_lbl = toga.Label(T["exercise"][self.lang], style=S_LBL())
        self.exercise = toga.Selection(items=list(EX_UI_TO_KEY[self.lang].keys()),
                                       value=list(EX_UI_TO_KEY[self.lang].keys())[0],
                                       style=S_INP(200))
        self.bw_lbl = toga.Label(T["bar_weight"][self.lang], style=S_LBL())
        self.bar_weight = toga.NumberInput(step=1, value=100, style=S_INP(160))
        self.reps_lbl = toga.Label(T["reps"][self.lang], style=S_LBL())
        self.reps = toga.NumberInput(step=1, value=5, style=S_INP(120))

        self.btn_bar = toga.Button(T["calc"][self.lang], on_press=self.calculate_bar, style=S_BTN())
        try:
            self.btn_bar.style.background_color = CLR_BTN_BG
            self.btn_bar.style.color = CLR_BTN_FG
        except Exception:
            pass

        self.bar_results_holder = toga.Box(style=S_COL())

        bar_rows = [
            toga.Box(children=[self.gender_b_lbl, self.gender_b], style=S_ROW()),
            toga.Box(children=[self.weight_b_lbl, self.weight_b], style=S_ROW()),
            toga.Box(children=[self.ex_lbl, self.exercise], style=S_ROW()),
            toga.Box(children=[self.bw_lbl, self.bar_weight], style=S_ROW()),
            toga.Box(children=[self.reps_lbl, self.reps], style=S_ROW()),
            toga.Box(children=[self.btn_bar], style=S_ROW()),
            self.bar_results_holder,
        ]
        self.bar_col = toga.Box(children=bar_rows, style=Pack(direction=COLUMN, flex=1))
        self.bar_page = toga.ScrollContainer(content=self.bar_col, horizontal=False, style=Pack(flex=1))

        # Tabs
        try:
            self.tabs = toga.OptionContainer(
                content=[(T["mode_erg"][self.lang], self.erg_page),
                         (T["mode_bar"][self.lang], self.bar_page)],
                style=Pack(flex=1)
            )
        except TypeError:
            self.tabs = toga.OptionContainer(
                content=[(self.erg_page, T["mode_erg"][self.lang]),
                         (self.bar_page, T["mode_bar"][self.lang])],
                style=Pack(flex=1)
            )
        try:
            self.tabs.on_select = self._on_tab_select
        except Exception:
            pass

        # Корень + заметный зазор между шапкой и вкладками
        spacer = toga.Box(style=Pack(height=16))
        root = toga.Box(style=Pack(direction=COLUMN, flex=1))
        root.add(header)
        root.add(spacer)
        root.add(self.tabs)

        # Показ полностью готового дерева
        self.main_window.content = root

        # Невидимый «мягкий нудж»
        self._nudge_scrollcontainers()
        if IS_IOS:
            loop = asyncio.get_event_loop()
            loop.call_later(0.02, self._nudge_scrollcontainers)
            loop.call_later(0.10, self._nudge_scrollcontainers)

        # FIX(iOS layout): Однократный «прогрев» скрытой вкладки «Штанга»
        if IS_IOS:
            self._ensure_bar_ready_once()

        # Тихие iOS-фиксы клавиатуры и синхронизации Selection
        self._apply_ios_keyboard_types()
        if IS_IOS:
            loop = asyncio.get_event_loop()
            loop.call_later(0.03, self._apply_ios_keyboard_types)
            loop.call_later(0.20, self._apply_ios_keyboard_types)
            try:
                idx_min = [row.value for row in list(self.min_sel.items)].index(self._min_value)
            except Exception:
                idx_min = None
            try:
                idx_sec = [row.value for row in list(self.sec_sel.items)].index(self._sec_value)
            except Exception:
                idx_sec = None
            loop.call_later(0.02, lambda: self._ios_sync_selection_display(self.min_sel, index=idx_min))
            loop.call_later(0.025, lambda: self._ios_sync_selection_display(self.sec_sel, index=idx_sec))

        self._erg_init_done = True

        # Финальный мягкий рефреш
        try:
            self._deep_refresh(self.main_window.content)
        except Exception:
            pass
        _force_layout_ios(self.main_window)

    # ---- Обработчик переключения вкладок (iOS) ----
    def _on_tab_select(self, widget, option=None):
        self._dismiss_ios_inputs()

        # Определяем, что выбран именно экран «Штанга»
        is_bar = False
        try:
            if option is self.bar_page or option is self.bar_col:
                is_bar = True
            elif hasattr(option, "content") and option.content is self.bar_page:
                is_bar = True
            elif hasattr(option, "text") and option.text == T["mode_bar"][self.lang]:
                is_bar = True
        except Exception:
            pass

        if IS_IOS and is_bar:
            # Один раз выполняем инициализацию лэйаута и убираем возможные блюры
            self._ensure_bar_ready_once()

        self._nudge_scrollcontainers()

    # ---- Обновление существующих заголовков (без пересчёта) ----
    def _update_existing_titles(self):
        if self.erg_tbl1_title_label is not None:
            self.erg_tbl1_title_label.text = T["erg_tbl1_title"][self.lang]
            try:
                self.erg_tbl1_title_label.refresh()
            except Exception:
                pass
        if self.erg_tbl2_title_label is not None:
            try:
                w = int(float(self.weight.value or 0))
            except Exception:
                w = 0
            self.erg_tbl2_title_label.text = T["erg_tbl2_title"][self.lang].format(w=w)
            try:
                self.erg_tbl2_title_label.refresh()
            except Exception:
                pass
        if self.bar_tbl_title_label is not None:
            self.bar_tbl_title_label.text = T["bar_tbl_title"][self.lang]
            try:
                self.bar_tbl_title_label.refresh()
            except Exception:
                pass
        _force_layout_ios(self.main_window)

    # ---- Handlers ----
    def _on_lang_change(self, widget):
        if self._updating:
            return

        self._updating = True
        try:
            self._dismiss_ios_inputs()

            # Сохраняем состояние (языконезависимо)
            old_lang = self.lang
            old_gender_key = GENDER_MAP[old_lang].get(self.gender.value, "male")
            old_gender_b_key = GENDER_MAP[old_lang].get(self.gender_b.value, "male")
            old_min = self._min_value
            old_sec = self._sec_value
            old_cen = self._cen_value
            old_ex_key = EX_UI_TO_KEY.get(old_lang, {}).get(self.exercise.value, None)

            # Новый язык
            inv = {v: k for k, v in LANG_LABEL.items()}
            self.lang = inv.get(self.lang_sel.value, "en")

            # Подставляем тексты
            self._apply_language_texts()

            # Восстанавливаем гендеры на обеих вкладках
            self.gender.items = GENDER_LABELS[self.lang]
            self.gender.value = GENDER_LABELS[self.lang][0 if old_gender_key == "female" else 1]
            self.gender_b.items = GENDER_LABELS[self.lang]
            self.gender_b.value = GENDER_LABELS[self.lang][0 if old_gender_b_key == "female" else 1]

            # Восстанавливаем упражнение
            self.exercise.items = list(EX_UI_TO_KEY[self.lang].keys())
            if old_ex_key is not None:
                new_ex_label = EX_KEY_TO_LABEL[self.lang].get(old_ex_key)
                items_values = [row.value for row in list(self.exercise.items)]
                if new_ex_label in items_values:
                    self.exercise.value = new_ex_label
                elif self.exercise.items:
                    self.exercise.value = list(self.exercise.items)[0].value

            # Восстанавливаем время
            self._min_value = old_min
            self._sec_value = old_sec
            self._cen_value = old_cen

            self.min_sel.value = old_min
            self._rebuild_time_selects(force_second_minute=False, preserve_sec=True)

            try:
                centis_now = [row.value for row in list(self.cen_sel.items)] or []
                if old_cen in centis_now:
                    self.cen_sel.value = old_cen
                    self._cen_value = old_cen
            except Exception:
                pass

            # Чистим результаты и слегка «пинаем» лэйаут
            self._clear_all_results()
            self._nudge_scrollcontainers()

            # После смены языка следующий заход на «Штангу» снова требует первичного фикс-прохода
            self._bar_needs_first_fix = True
            if IS_IOS:
                # На всякий случай подчистим возможные блюры уже сейчас
                self._ios_strip_global_blurs()

            # Второй проход (отложенно): синхронизация визуала на Эргометре
            def _second_pass():
                self._clear_all_results()
                self._update_existing_titles()
                self._apply_ios_keyboard_types()
                self._ios_sync_selection_display(self.min_sel)
                self._ios_sync_selection_display(self.sec_sel)

            asyncio.get_event_loop().call_later(0.015, _second_pass)

            # Финальный рефреш
            self._deep_refresh(self.main_window.content)
            _force_layout_ios(self.main_window)
            self._apply_ios_keyboard_types()

        finally:
            self._updating = False

    def _apply_language_texts(self):
        if self.header_lang_label is not None:
            self.header_lang_label.text = T["language"][self.lang]

        # Эргометр
        self.gender_lbl.text = T["gender"][self.lang]
        self.weight_lbl.text = T["weight"][self.lang]
        self.distance_lbl.text = T["distance"][self.lang]
        self.time_lbl.text = T["time_compact"][self.lang]  # UI: compact time row
        self.btn_erg.text = T["calc"][self.lang]
        self.gender.items = GENDER_LABELS[self.lang]

        # Штанга
        self.gender_b_lbl.text = T["gender"][self.lang]
        self.weight_b_lbl.text = T["weight"][self.lang]
        self.gender_b.items = GENDER_LABELS[self.lang]

        self.ex_lbl.text = T["exercise"][self.lang]
        self.bw_lbl.text = T["bar_weight"][self.lang]
        self.reps_lbl.text = T["reps"][self.lang]
        self.btn_bar.text = T["calc"][self.lang]

        # Заголовки вкладок
        try:
            items_tabs = list(self.tabs.content)
            items_tabs[0].text = T["mode_erg"][self.lang]
            items_tabs[1].text = T["mode_bar"][self.lang]
        except Exception:
            pass

    def _set_exercise_items(self):
        current = self.exercise.value
        items = list(EX_UI_TO_KEY[self.lang].keys())
        self.exercise.items = items
        self.exercise.value = current if current in items else (items[0] if items else None)

    def _on_gender_change(self, widget):
        if self._updating:
            return
        self._rebuild_time_selects(force_second_minute=True, preserve_sec=False)
        try:
            rows = list(self.min_sel.items) or []
            if len(rows) >= 2:
                self.min_sel.value = rows[1].value
                self._min_value = rows[1].value
        except Exception:
            pass
        self._ios_sync_selection_display(self.min_sel, index=1)
        self._cen_value = "0"
        try:
            self.cen_sel.value = "0"
        except Exception:
            pass
        _force_layout_ios(self.main_window)

    def _on_distance_change(self, widget):
        if self._updating:
            return
        self._rebuild_time_selects(force_second_minute=True, preserve_sec=False)
        try:
            rows = list(self.min_sel.items) or []
            if len(rows) >= 2:
                self.min_sel.value = rows[1].value
                self._min_value = rows[1].value
        except Exception:
            pass
        self._ios_sync_selection_display(self.min_sel, index=1)
        self._cen_value = "0"
        try:
            self.cen_sel.value = "0"
        except Exception:
            pass
        _force_layout_ios(self.main_window)

    def _on_minute_change(self, widget):
        if self._updating:
            return
        # Перестроим список секунд для выбранной минуты, С ОХРАНОЙ текущего значения
        g_key = GENDER_MAP[self.lang].get(self.gender.value, "male")
        dist = int(self.distance.value)
        dist_data = get_distance_data(g_key, dist, self.rowing_data)
        _, sec_map = parse_available_times(dist_data)

        self._min_value = self.min_sel.value
        seconds = sec_map.get(self._min_value, ["00"])

        old_sec = self._sec_value
        self._set_selection_items_preserve(self.sec_sel, seconds, old_sec)
        # Зафиксируем фактическое значение (вдруг Toga поправила его)
        try:
            self._sec_value = self.sec_sel.value
        except Exception:
            pass

        # iOS: синхронизируем визуально
        self._ios_sync_selection_display(self.sec_sel)

    def _on_second_change(self, widget):
        if self._updating:
            return
        try:
            self._sec_value = self.sec_sel.value
        except Exception:
            pass

    def _on_centi_change(self, widget):
        if self._updating:
            return
        try:
            self._cen_value = self.cen_sel.value
        except Exception:
            pass

    # ---- Минуты/секунды ----
    def _rebuild_time_selects(self, force_second_minute: bool = False, preserve_sec: bool = True):
        g_key = GENDER_MAP[self.lang].get(self.gender.value, "male")
        dist = int(self.distance.value)
        dist_data = get_distance_data(g_key, dist, self.rowing_data)
        if not dist_data:
            self.min_sel.items = ["00"]; self.min_sel.value = "00"
            self.sec_sel.items = ["00"]; self.sec_sel.value = "00"
            self._min_value = "00"
            self._sec_value = "00"
            return

        minutes, sec_map = parse_available_times(dist_data)

        if force_second_minute:
            default_min = minutes[1] if len(minutes) >= 2 else minutes[0]
        else:
            default_min = minutes[1] if len(minutes) >= 2 else minutes[0]
            if self._erg_init_done and self._min_value in minutes:
                default_min = self._min_value

        self.min_sel.items = minutes
        self.min_sel.value = default_min
        self._min_value = default_min

        seconds = sec_map.get(default_min, ["00"])

        if force_second_minute and not preserve_sec:
            # Жёсткий режим: выбрать дефолт и зафиксировать
            default_sec = seconds[0]
            self._set_selection_items_preserve(self.sec_sel, seconds, default_sec)
            self._sec_value = default_sec
        else:
            # Сохранить текущее значение секунд
            self._set_selection_items_preserve(self.sec_sel, seconds, self._sec_value)
            try:
                self._sec_value = self.sec_sel.value
            except Exception:
                pass

    # ---- Расчёты ----
    def calculate_erg(self, widget):
        self._dismiss_ios_inputs()
        try:
            bw = float(self.weight.value or 0)
            if not (40 <= bw <= 140):
                self._info(T["err_weight"][self.lang]); return

            g_key = GENDER_MAP[self.lang].get(self.gender.value, "male")
            dist = int(self.distance.value)
            dist_data = get_distance_data(g_key, dist, self.rowing_data)
            if not dist_data: self._info(T["err_no_data"][self.lang]); return

            mm = self._min_value
            ss = self._sec_value
            cc = self._cen_value

            t_norm = (f"{mm}:{ss}.{cc}" if str(cc) not in ("0", "00") else f"{mm}:{ss}")
            dist_data_time = (
                dist_data.get(t_norm)
                or dist_data.get(t_norm.lstrip("0"))
                or dist_data.get(f"{mm}:{ss}")
                or dist_data.get(f"{mm}:{ss}".lstrip("0"))
            )
            if not dist_data_time: self._info(T["err_time_range"][self.lang]); return

            percent = dist_data_time.get("percent")
            strength = get_strength_data(g_key, bw, self.strength_data_all)
            if not strength: self._info(T["err_no_strength"][self.lang]); return

            rows1, keys = [], [k for k in dist_data_time.keys() if k != "percent"]
            kmap = {meters_from_key(k): dist_data_time[k] for k in keys}
            for m in SHOW_DISTANCES:
                if m in kmap:
                    t = kmap[m]
                    rows1.append([f"{m} m", f"{t}", get_split_500m(m, t)])

            rows2, labels = [], EX_KEY_TO_LABEL[self.lang]
            for ex_key, ui_label in labels.items():
                kilo = strength.get(ex_key, {}).get(percent)
                if kilo == "1":
                    vmap = strength.get(ex_key, {})
                    kilo = round((float(kilo) + float(vmap.get("1"))) / 2, 2)
                rows2.append([ui_label, f"{kilo} kg"])

            self.erg_results_holder.children.clear()

            self.erg_tbl1_title_label = toga.Label(
                T["erg_tbl1_title"][self.lang],
                style=Pack(font_size=F_LABEL, color=CLR_ACCENT, padding_top=6, padding_bottom=2)
            )
            self.erg_results_holder.add(toga.Box(children=[self.erg_tbl1_title_label], style=S_ROW()))
            self.erg_results_holder.add(make_table(rows1, col_flex=[1, 1, 1]))

            self.erg_tbl2_title_label = toga.Label(
                T["erg_tbl2_title"][self.lang].format(w=int(bw)),
                style=Pack(font_size=F_LABEL, color=CLR_ACCENT, padding_top=6, padding_bottom=2)
            )
            self.erg_results_holder.add(toga.Box(children=[self.erg_tbl2_title_label], style=S_ROW()))
            self.erg_results_holder.add(make_table(rows2, col_flex=[1, 1]))

            # После расчёта на Эргометре подстрахуем готовность «Штанги»
            if IS_IOS:
                self._bar_needs_first_fix = True  # на случай смены данных — реинициализируем при заходе

        except Exception as e:
            self._info(str(e))

    def calculate_bar(self, widget):
        self._dismiss_ios_inputs()
        try:
            bw = float(self.weight_b.value or 0)
            if not (40 <= bw <= 140):
                self._info(T["err_weight"][self.lang]); return

            bar_w = float(self.bar_weight.value or 0)
            if not (1 <= bar_w <= 700):
                self._info(T["err_bar_weight"][self.lang]); return

            reps = int(self.reps.value or 0)
            if not (1 <= reps <= 30):
                self._info(T["err_reps"][self.lang]); return

            rep_max = round((bar_w / REPS_TABLE[reps]) * 100, 2)

            g_key = GENDER_MAP[self.lang].get(self.gender_b.value, "male")
            strength_for_user = get_strength_data(g_key, bw, self.strength_data_all)
            if not strength_for_user: self._info(T["err_no_strength"][self.lang]); return

            ex_key = EX_UI_TO_KEY[self.lang][self.exercise.value]
            ex_table = strength_for_user.get(ex_key, {})
            i_percent = None
            for pct_str, val in ex_table.items():
                if float(val) <= rep_max:
                    i_percent = float(pct_str)
                else:
                    break
            if i_percent is None: self._info(T["err_1rm_map"][self.lang]); return

            distance_data = get_distance_data(g_key, 2000, self.rowing_data)
            km2_res = None
            for k, v in distance_data.items():
                km2_res = k
                if float(v.get("percent")) < i_percent:
                    break

            rows = [
                [T["tbl_1rm"][self.lang], f"{rep_max} кг" if self.lang == "ru" else f"{rep_max} kg"],
                [T["tbl_2k"][self.lang], km2_res],
            ]

            self.bar_results_holder.children.clear()

            self.bar_tbl_title_label = toga.Label(
                T["bar_tbl_title"][self.lang],
                style=Pack(font_size=F_LABEL, color=CLR_ACCENT, padding_top=6, padding_bottom=2)
            )
            self.bar_results_holder.add(toga.Box(children=[self.bar_tbl_title_label], style=S_ROW()))
            self.bar_results_holder.add(make_table(rows, col_flex=[1, 1]))

        except Exception as e:
            self._info(str(e))


def main():
    return RowStrengthApp("RowStrength", "com.rowstrength")
