import sys
import re
import json
from importlib import resources
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

# ---------- Константы ----------
DISTANCES = [500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000]
GENDERS_UI = {"ж": "female", "м": "male"}
EXERCISES_UI_TO_KEY = {"жим": "bench-press", "присед": "squat", "тяга": "deadlift"}
EXERCISES_KEY_TO_RU = {"bench-press": "жиме", "squat": "приседе", "deadlift": "становой тяге"}
MODE_CHOICES = ["Эргометр", "Штанга"]

REPS_TABLE = {
    1: 100, 2: 97, 3: 94, 4: 92, 5: 89, 6: 86, 7: 83, 8: 81, 9: 78, 10: 75,
    11: 73, 12: 71, 13: 70, 14: 68, 15: 67, 16: 65, 17: 64, 18: 63, 19: 61,
    20: 60, 21: 59, 22: 58, 23: 57, 24: 56, 25: 55, 26: 54, 27: 53, 28: 52,
    29: 51, 30: 50
}

# ---------- Стили (крупнее и «воздушнее» под iOS) ----------
IS_IOS = (sys.platform == "ios")
F_HEAD = 22 if IS_IOS else 18
F_LABEL = 16 if IS_IOS else 14
F_INPUT = 16 if IS_IOS else 14
PAD_MAIN = 18 if IS_IOS else 14
GAP_MAIN = 14 if IS_IOS else 10

S_MAIN = Pack(direction=COLUMN, padding=PAD_MAIN, gap=GAP_MAIN)
S_ROW = Pack(direction=ROW, gap=10, padding_bottom=6)
S_HEAD = Pack(font_size=F_HEAD, padding_bottom=6)
S_LABEL = Pack(font_size=F_LABEL, padding_right=8)
S_INPUT = Pack(font_size=F_INPUT)
S_BTN = Pack(padding_top=6, padding_bottom=6)
S_OUT = Pack(height=140, font_size=F_INPUT, padding_top=4)


# ---------- Утилиты ----------
def load_json_from_package(filename: str):
    with resources.files(__package__).joinpath("data").joinpath(filename).open("r", encoding="utf-8") as f:
        return json.load(f)


def get_distance_data(i_gender, i_distance, rowing_data):
    return rowing_data.get(i_gender, {}).get(str(i_distance), {})


def get_strength_data(i_gender, i_weight, strength_data):
    return strength_data.get(i_gender, {}).get(str(i_weight), {})


def _parse_time_range_from_data(distance_data):
    """Вернёт (min_mm, min_ss), (max_mm, max_ss) по ключам 'MM:SS' из distance_data."""
    times = []
    for k in distance_data.keys():
        m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", k)
        if m:
            times.append((int(m.group(1)), int(m.group(2))))
    if not times:
        return (0, 0), (59, 59)
    min_mm = min(mm for mm, _ in times)
    max_mm = max(mm for mm, _ in times)
    # секунды для мин/макс минут (нам уже не критично, но оставим для полноты)
    min_ss = min(ss for mm, ss in times if mm == min_mm)
    max_ss = max(ss for mm, ss in times if mm == max_mm)
    return (min_mm, min_ss), (max_mm, max_ss)


def _two(n: int) -> str:
    return f"{n:02d}"


# ---------- Приложение ----------
class RowStrengthApp(toga.App):
    def startup(self):
        # Данные
        self.rowing_data = load_json_from_package("data_for_rowing_app.json")
        self.strength_data_all = load_json_from_package("data_for_strength_app.json")

        # Заголовок
        title = toga.Label("RowStrength", style=S_HEAD)

        # Режим: iOS → SegmentedButton, иначе Selection
        self.mode_widget = self._make_mode_widget()

        # Общие поля
        self.gender = toga.Selection(items=["ж", "м"], value="м", on_change=self._on_gender_changed, style=S_INPUT)
        self.weight = toga.NumberInput(step=1, min=40, max=140, value=80, style=S_INPUT)

        # Режим 1 (Эргометр) — селекты времени
        self.distance = toga.Selection(items=[str(d) for d in DISTANCES], value="2000",
                                       on_change=self._on_distance_changed, style=S_INPUT)
        self.time_min = toga.Selection(items=["06"], value="06", on_change=self._on_time_min_changed, style=S_INPUT)
        # секунды всегда 01..59
        self.time_sec = toga.Selection(items=[_two(i) for i in range(1, 60)], value="01", style=S_INPUT)
        # сотые — 00..99
        self.time_ms = toga.Selection(items=[_two(i) for i in range(10)], value="0", style=S_INPUT)

        self.res1_title = toga.Label("⏱ Результаты по дистанциям", style=S_LABEL)
        self.res1_output = toga.MultilineTextInput(readonly=True, style=S_OUT)
        self.res1_strength_title = toga.Label("🏋️ Эквиваленты в штанге", style=S_LABEL)
        self.res1_output_strength = toga.MultilineTextInput(readonly=True, style=S_OUT)

        # Режим 2 (Штанга)
        self.exercise = toga.Selection(items=[i.capitalize() for i in list(EXERCISES_UI_TO_KEY.keys())],
                                       value="Жим", style=S_INPUT)
        self.bar_weight = toga.NumberInput(step=1, min=1, value=100, style=S_INPUT)
        self.reps = toga.NumberInput(step=1, min=1, max=30, value=5, style=S_INPUT)
        self.res2_title = toga.Label("🏋️ 1ПМ и эквивалент 2 км", style=S_LABEL)
        self.res2_output = toga.MultilineTextInput(readonly=True, style=S_OUT)

        # Кнопка
        self.calc_button = toga.Button("Рассчитать", on_press=self.calculate, style=S_BTN)

        # Компоновка — крупные отступы, структурированные блоки
        head_row = toga.Box(children=[title], style=Pack(direction=ROW, padding_bottom=8))

        mode_row = toga.Box(children=[toga.Label("Режим:", style=S_LABEL), self.mode_widget], style=S_ROW)
        common_row = toga.Box(children=[toga.Label("Пол:", style=S_LABEL), self.gender,
                                        toga.Label("Вес (кг):", style=S_LABEL), self.weight], style=S_ROW)

        # Блок ввода для «Эргометр»: дистанция + время (мин/сек/сотые)
        self.mode1_box = toga.Box(
            children=[
                toga.Label("Дистанция:", style=S_LABEL), self.distance,
                toga.Label("Мин:", style=S_LABEL), self.time_min,
                toga.Label("Сек:", style=S_LABEL), self.time_sec,
                toga.Label("Сотые:", style=S_LABEL), self.time_ms,
            ],
            style=S_ROW
        )
        # Блок ввода для «Штанга»
        self.mode2_box = toga.Box(
            children=[toga.Label("Упражнение:", style=S_LABEL), self.exercise,
                      toga.Label("Вес на штанге (кг):", style=S_LABEL), self.bar_weight,
                      toga.Label("Повторы:", style=S_LABEL), self.reps],
            style=S_ROW
        )

        # Результаты — «карточки» для режимов
        self.mode1_results_box = toga.Box(
            children=[self.res1_title, self.res1_output, self.res1_strength_title, self.res1_output_strength],
            style=Pack(direction=COLUMN, gap=10, padding_top=4)
        )
        self.mode2_results_box = toga.Box(
            children=[self.res2_title, self.res2_output],
            style=Pack(direction=COLUMN, gap=10, padding_top=4)
        )

        main_box = toga.Box(
            children=[head_row, mode_row, common_row, self.mode1_box, self.mode2_box, self.calc_button,
                      self.mode1_results_box, self.mode2_results_box],
            style=S_MAIN
        )

        # Инициализация диапазона минут под дефолтные пол/дистанцию
        self._rebuild_time_selects()

        # Показ/скрытие нужных блоков
        self._on_mode_changed(None)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    # ---- вспомогательные методы UI ----
    def _make_mode_widget(self):
        """Создание переключателя режима: iOS -> SegmentedButton, иначе Selection."""
        if IS_IOS and hasattr(toga, "SegmentedButton"):
            widget = toga.SegmentedButton(items=MODE_CHOICES, on_change=self._on_mode_changed)
            widget.value = MODE_CHOICES[0]
            return widget
        else:
            return toga.Selection(items=MODE_CHOICES, value=MODE_CHOICES[0],
                                  on_change=self._on_mode_changed, style=S_INPUT)

    def _get_mode_value(self) -> str:
        return self.mode_widget.value

    def _on_mode_changed(self, widget):
        if self._get_mode_value() == MODE_CHOICES[0]:
            # Эргометр
            self.mode1_box.style.update(visibility="visible")
            self.mode1_results_box.style.update(visibility="visible")
            self.mode2_box.style.update(visibility="hidden")
            self.mode2_results_box.style.update(visibility="hidden")
        else:
            # Штанга
            self.mode1_box.style.update(visibility="hidden")
            self.mode1_results_box.style.update(visibility="hidden")
            self.mode2_box.style.update(visibility="visible")
            self.mode2_results_box.style.update(visibility="visible")

    def _on_distance_changed(self, widget):
        self._rebuild_time_selects()

    def _on_gender_changed(self, widget):
        self._rebuild_time_selects()

    def _on_time_min_changed(self, widget):
        # Теперь секунды всегда 01..59 — ничего пересчитывать не нужно
        pass

    def _rebuild_time_selects(self):
        """Перестроить список минут исходя из диапазона времени в данных для текущей дистанции и выбранного пола.
           Секунды фиксированы как 01..59.
        """
        # Пол и дистанция
        try:
            g_key = GENDERS_UI[self.gender.value]
        except Exception:
            g_key = "male"
        distance = int(self.distance.value)

        distance_data = get_distance_data(g_key, distance, self.rowing_data)
        (min_mm, _min_ss), (max_mm, _max_ss) = _parse_time_range_from_data(distance_data)

        # Если данных нет — используем безопасный диапазон минут
        if not distance_data:
            min_mm, max_mm = 0, 59

        # Минуты: от min_mm до max_mm
        minutes_items = [_two(i) for i in range(min_mm, max_mm + 1)]
        prev_min = self.time_min.value if self.time_min.value in minutes_items else _two(min_mm)
        self.time_min.items = minutes_items
        self.time_min.value = prev_min

        # Секунды всегда 01..59
        sec_items = [_two(i) for i in range(1, 60)]
        prev_sec = self.time_sec.value if self.time_sec.value in sec_items else "01"
        self.time_sec.items = sec_items
        self.time_sec.value = prev_sec

        # Сотые — оставляем неизменными (00..99)
        if self.time_ms.value is None:
            self.time_ms.value = "00"

    # ---- бизнес-логика ----
    def calculate(self, widget):

        def _meters_from_key(k) -> int:
            m = re.search(r"\d+", str(k))
            return int(m.group()) if m else 0

        try:
            g_key = GENDERS_UI[self.gender.value]
            weight = int(self.weight.value)

            if self._get_mode_value() == MODE_CHOICES[0]:
                # --- Эргометр ---
                distance = int(self.distance.value)
                distance_data = get_distance_data(g_key, distance, self.rowing_data)
                if not distance_data:
                    raise ValueError("Нет данных по выбранной дистанции/полу")

                # Собираем нормализованное время из селектов
                t_norm = f"{self.time_min.value}:{self.time_sec.value}"
                distance_data_time = distance_data.get(t_norm) or distance_data.get(t_norm.lstrip("0"))
                if not distance_data_time:
                    times_str = list(distance_data.keys())
                    raise ValueError(f"Время вне диапазона. Доступно: от {times_str[0]} до {times_str[-1]}")

                percent = distance_data_time.get("percent")
                strength = get_strength_data(g_key, weight, self.strength_data_all)
                if not strength:
                    raise ValueError("Нет силовых данных для указанного веса")

                # Блок 1: результаты на дистанциях
                lines_dist = []
                keys = [kk for kk in distance_data_time.keys() if kk != "percent"]
                keys.sort(key=_meters_from_key)
                for k in keys:
                    v = distance_data_time[k]
                    meters = _meters_from_key(k)  # нормализуем '500m' -> 500
                    lines_dist.append(f"{meters} м — {v}.00")
                self.res1_output.value = "\n".join(lines_dist)

                # Блок 2: эквиваленты в штанге
                lines_str = []
                for ex_key, ex_label_ru in EXERCISES_KEY_TO_RU.items():
                    kilo = strength.get(ex_key, {}).get(percent)
                    if kilo == "1":
                        vmap = strength.get(ex_key, {})
                        kilo = round((float(kilo) + float(vmap.get("1"))) / 2, 2)
                    lines_str.append(f"{ex_label_ru.title()}: {kilo} кг")
                self.res1_output_strength.value = "\n".join(lines_str)

            else:
                # --- Штанга ---
                ex_key = EXERCISES_UI_TO_KEY[self.exercise.value.lower()]
                bar_w = float(self.bar_weight.value)
                reps = int(self.reps.value)
                if reps not in REPS_TABLE:
                    raise ValueError("Поддерживаются повторы 1..30")

                rep_max = round((bar_w / REPS_TABLE[reps]) * 100, 2)

                strength_for_user = get_strength_data(g_key, weight, self.strength_data_all)
                if not strength_for_user:
                    raise ValueError("Нет силовых данных для указанного веса")

                ex_table = strength_for_user.get(ex_key, {})
                i_percent = None
                for pct_str, val in ex_table.items():
                    if float(val) <= rep_max:
                        i_percent = float(pct_str)
                    else:
                        break
                if i_percent is None:
                    raise ValueError("Не удалось сопоставить проценты для 1ПМ")

                distance_data = get_distance_data(g_key, 2000, self.rowing_data)
                km2_res = None
                for k, v in distance_data.items():
                    km2_res = k
                    if float(v.get("percent")) < i_percent:
                        break

                self.res2_output.value = "\n".join([
                    f"Оценка 1ПМ: {rep_max} кг",
                    f"Эквивалент на 2 км: {km2_res}"
                ])

        except Exception as e:
            try:
                self.main_window.error_dialog("Ошибка", str(e))
            except Exception:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print("Ошибка:", e, f"{exc_tb.tb_lineno}")


def main():
    return RowStrengthApp("RowStrength", "com.rowstrength")
