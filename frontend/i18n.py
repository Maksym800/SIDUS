"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import streamlit as st

from data import catalog

LANGUAGES = ("en", "uk")
DEFAULT_LANGUAGE = "en"

TEXTS: dict[str, tuple[str, str]] = {
    "app.title": ("Crew health monitor", "Монітор здоров'я екіпажу"),
    "topbar.environment": ("Mission environment", "Середовище місії"),
    "topbar.language_help": ("Switch the interface language", "Змінити мову інтерфейсу"),
    "lang.switch_to": ("Українська", "English"),
    "env.earth": ("Earth", "Земля"),
    "env.mars": ("Mars", "Марс"),
    "env.moon": ("Moon", "Місяць"),
    "env.deep_space": ("Deep space (microgravity)", "Далекий космос (мікрогравітація)"),
    "env.orbit": ("Orbit (microgravity)", "Орбіта (мікрогравітація)"),

    "menu.heading": ("Choose your profile", "Оберіть свій профіль"),
    "menu.intro": ("Open your profile to see your status and enter today's measurements.",
                   "Відкрийте свій профіль, щоб переглянути стан і внести сьогоднішні показники."),
    "menu.empty": ("There are no profiles yet. Create the first one to record a personal baseline.",
                   "Профілів ще немає. Створіть перший, щоб зафіксувати особисту норму."),
    "menu.create": ("Create profile", "Створити профіль"),
    "menu.open": ("Open profile", "Відкрити профіль"),
    "menu.age": ("Age {age}", "Вік: {age}"),
    "menu.flight_day": ("Flight day {day}", "{day}-й день польоту"),
    "menu.preflight": ("Days to launch: {days}", "Днів до старту: {days}"),
    "menu.last_update": ("Data updated {when}", "Дані оновлено {when}"),
    "menu.stale": ("No data update for more than 24 hours",
                   "Дані не оновлювалися понад 24 години"),
    "menu.stale_legend": ("The exclamation mark means the data has not been updated in the last 24 hours.",
                          "Знак оклику означає, що дані не оновлювалися протягом останніх 24 годин."),

    "create.heading": ("New astronaut profile", "Новий профіль астронавта"),
    "create.intro": ("Enter values measured on Earth while healthy, rested and calm. They become "
                     "your personal norm, and every later reading is compared with them.",
                     "Введіть показники, виміряні на Землі у здоровому, відпочилому та спокійному "
                     "стані. Вони стануть вашою особистою нормою, з якою порівнюватимуться всі "
                     "наступні вимірювання."),
    "create.name": ("Full name", "Ім'я та прізвище"),
    "create.age": ("Age", "Вік"),
    "create.flight_start": ("Flight start date", "Дата початку польоту"),
    "create.baseline_heading": ("Baseline measured on Earth", "Базові показники на Землі"),
    "create.prefilled_note": ("Typical values are filled in to save typing. Replace them with "
                              "your own measurements.",
                              "Типові значення підставлено для зручності. Замініть їх власними "
                              "вимірюваннями."),
    "create.game_expander": ("Take the coordination test now (optional)",
                             "Пройти тест на координацію зараз (необов'язково)"),
    "create.game_hint": ("The result is copied into the coordination field of the form. You can "
                         "also type a value by hand.",
                         "Результат буде підставлено в поле координації у формі. Значення можна "
                         "також ввести вручну."),
    "create.game_filled": ("Test result {score}% is filled in below.",
                           "Результат тесту {score} % підставлено нижче."),
    "create.submit": ("Create profile", "Створити профіль"),
    "create.cancel": ("Cancel", "Скасувати"),
    "create.error_name_empty": ("Enter a name to create the profile.",
                                "Введіть ім'я, щоб створити профіль."),
    "create.error_name_taken": ("A profile named “{name}” already exists. Use a different name.",
                                "Профіль з іменем «{name}» уже існує. Вкажіть інше ім'я."),
    "create.created": ("Profile created. These values are now your baseline.",
                       "Профіль створено. Ці показники тепер є вашою нормою."),

    "form.glucose_unit": ("Glucose unit", "Одиниці глюкози"),
    "form.error_values": ("The values could not be saved: {error}",
                          "Не вдалося зберегти показники: {error}"),
    "group.body": ("Body", "Тіло"),
    "group.cardio": ("Heart and circulation", "Серце та кровообіг"),
    "group.vision": ("Vision", "Зір"),
    "group.sleep": ("Sleep", "Сон"),
    "group.muscle": ("Muscles", "М'язи"),
    "group.vitals": ("Temperature and breathing", "Температура та дихання"),
    "group.neuro": ("Coordination", "Координація"),
    "group.blood": ("Blood and urine tests", "Аналізи крові та сечі"),
    "group.psych": ("Mood and stress", "Настрій і стрес"),
    "group.radiation": ("Radiation", "Радіація"),

    "metric.mass_kg": ("Body mass", "Маса тіла"),
    "metric.heart_rate_bpm": ("Heart rate (pulse)", "Частота серцевих скорочень (пульс)"),
    "metric.bp_systolic": ("Systolic blood pressure", "Систолічний тиск"),
    "metric.bp_diastolic": ("Diastolic blood pressure", "Діастолічний тиск"),
    "metric.ecg_rhythm": ("Heart rhythm (ECG)", "Серцевий ритм (ЕКГ)"),
    "metric.hrv_rmssd_ms": ("Heart-rate variability (HRV)", "Варіабельність серцевого ритму (ВСР)"),
    "metric.blood_flow_cm_s": ("Blood flow velocity (jugular vein)",
                               "Швидкість кровотоку (яремна вена)"),
    "metric.vascular_condition": ("Vessel condition (ultrasound)", "Стан судин (УЗД)"),
    "metric.vision_clear": ("Vision sharp and clear", "Зір гострий і чіткий"),
    "metric.sleep_hours": ("Sleep duration", "Тривалість сну"),
    "metric.sleep_efficiency_pct": ("Sleep efficiency", "Ефективність сну"),
    "metric.muscle_thickness_mm": ("Muscle thickness (thigh, ultrasound)",
                                   "Товщина м'яза (стегно, УЗД)"),
    "metric.muscle_structure": ("Muscle structure (ultrasound)", "Структура м'яза (УЗД)"),
    "metric.body_temp_c": ("Body temperature", "Температура тіла"),
    "metric.spo2_pct": ("Blood oxygen saturation (SpO₂)", "Сатурація крові (SpO₂)"),
    "metric.coordination_pct": ("Coordination and reaction speed",
                                "Координація та швидкість реакції"),
    "metric.glucose_mmol_l": ("Blood glucose", "Глюкоза крові"),
    "metric.cortisol_nmol_l": ("Cortisol (stress marker)", "Кортизол (маркер стресу)"),
    "metric.viral_activation": ("Signs of viral activation", "Ознаки активації вірусів"),
    "metric.calcium_mmol_l": ("Blood calcium (rapid test)", "Кальцій крові (експрес-тест)"),
    "metric.bone_resorption_ntx": ("Bone resorption marker (urine NTx)",
                                   "Маркер резорбції кістки (NTx у сечі)"),
    "metric.mood_score": ("Mood right now", "Настрій зараз"),
    "metric.stress_score": ("Stress level right now", "Рівень стресу зараз"),
    "metric.radiation_total_msv": ("Accumulated radiation dose", "Накопичена доза опромінення"),
    "metric.neutron_rate_usv_h": ("Neutron dose rate", "Потужність дози нейтронів"),

    "question.vision_clear": ("Is your vision sharp and clear?", "Чи зір гострий і чіткий?"),

    "help.hrv_rmssd_ms": ("RMSSD from a 5-minute recording at rest.",
                          "RMSSD за 5-хвилинним записом у спокої."),
    "help.blood_flow_cm_s": ("Peak flow velocity in the internal jugular vein, measured by "
                             "Doppler ultrasound.",
                             "Пікова швидкість кровотоку у внутрішній яремній вені за даними "
                             "доплерівського УЗД."),
    "help.sleep_efficiency_pct": ("Share of the time in bed that you were actually asleep.",
                                  "Частка часу в ліжку, проведена уві сні."),
    "help.coordination_pct": ("Result of the coordination test, or your own estimate if you "
                              "skip the test.",
                              "Результат тесту на координацію або власна оцінка, якщо ви "
                              "пропускаєте тест."),
    "help.cortisol_nmol_l": ("Measure at the same time of day as your baseline.",
                             "Вимірюйте в той самий час доби, що й базове значення."),
    "help.bone_resorption_ntx": ("Rapid urine test for N-telopeptide.",
                                 "Експрес-тест сечі на N-телопептид."),
    "help.mood_score": ("1 is very low, 10 is excellent.", "1 — дуже поганий, 10 — чудовий."),
    "help.stress_score": ("1 is calm, 10 is extreme stress.",
                          "1 — спокій, 10 — надзвичайний стрес."),
    "help.radiation_total_msv": ("Career total from your personal dosimeter.",
                                 "Сумарна доза за кар'єру за даними персонального дозиметра."),
    "help.neutron_rate_usv_h": ("Current reading of the neutron dosimeter.",
                                "Поточний показник нейтронного дозиметра."),

    "option.ecg_rhythm.0": ("Regular", "Регулярний"),
    "option.ecg_rhythm.1": ("Occasional irregular beats", "Поодинокі порушення ритму"),
    "option.ecg_rhythm.2": ("Persistent arrhythmia", "Стійка аритмія"),
    "option.vascular_condition.0": ("Normal flow", "Нормальний кровотік"),
    "option.vascular_condition.1": ("Stagnant or reversed flow", "Застійний або зворотний кровотік"),
    "option.vascular_condition.2": ("Signs of a clot", "Ознаки тромбу"),
    "option.vision_clear.1": ("Yes", "Так"),
    "option.vision_clear.0": ("No", "Ні"),
    "option.muscle_structure.0": ("Normal", "Нормальна"),
    "option.muscle_structure.1": ("Moderate changes", "Помірні зміни"),
    "option.muscle_structure.2": ("Pronounced changes", "Виражені зміни"),
    "option.viral_activation.0": ("Not noticed", "Не помічено"),
    "option.viral_activation.1": ("Noticed", "Помічено"),

    "unit.kg": ("kg", "кг"),
    "unit.bpm": ("bpm", "уд/хв"),
    "unit.mmhg": ("mmHg", "мм рт. ст."),
    "unit.ms": ("ms", "мс"),
    "unit.cm_s": ("cm/s", "см/с"),
    "unit.h": ("h", "год"),
    "unit.pct": ("%", "%"),
    "unit.mm": ("mm", "мм"),
    "unit.celsius": ("°C", "°C"),
    "unit.mmol_l": ("mmol/L", "ммоль/л"),
    "unit.mg_dl": ("mg/dL", "мг/дл"),
    "unit.nmol_l": ("nmol/L", "нмоль/л"),
    "unit.ntx": ("nmol BCE/mmol creatinine", "нмоль BCE/ммоль креатиніну"),
    "unit.msv": ("mSv", "мЗв"),
    "unit.usv_h": ("µSv/h", "мкЗв/год"),
    "unit.points": ("of 10", "з 10"),

    "astro.back": ("Back to crew", "До списку екіпажу"),
    "astro.flight_day": ("Flight day {day}, {stage}", "{day}-й день польоту, {stage}"),
    "astro.preflight": ("Days to launch: {days}", "Днів до старту: {days}"),
    "astro.updated": ("Metrics entered {when}", "Показники внесено {when}"),
    "astro.stale_warning": ("Your data has not been updated for more than 24 hours. Enter "
                            "today's measurements.",
                            "Ваші дані не оновлювалися понад 24 години. Внесіть сьогоднішні "
                            "показники."),
    "stage.preflight": ("pre-flight preparation", "передполітна підготовка"),
    "stage.adaptation": ("adaptation to flight", "адаптація до польоту"),
    "stage.main": ("main phase", "основний етап"),
    "stage.long_duration": ("long-duration phase", "етап тривалого польоту"),

    "astro.assessment_heading": ("Health assessment", "Оцінка стану здоров'я"),
    "astro.all_clear_title": ("No suspected pathologies", "Підозр на патології немає"),
    "astro.all_clear_body": ("Every tracked metric is within your personal norm for this "
                             "environment.",
                             "Усі показники в межах вашої особистої норми для цього середовища."),
    "astro.assessed_note": ("Assessed {when} for the environment “{env}”, from the metrics "
                            "entered {entry_when}.",
                            "Оцінку виконано {when} для середовища «{env}» за показниками, "
                            "внесеними {entry_when}."),
    "astro.evidence": ("{label}: {value} (baseline {baseline})",
                       "{label}: {value} (норма {baseline})"),
    "astro.evidence_plain": ("{label}: {value}", "{label}: {value}"),
    "astro.advice_label": ("What to do", "Що робити"),
    "astro.disclaimer": ("These are screening suggestions, not a medical diagnosis. Confirm "
                         "every finding with the flight surgeon.",
                         "Це скринінгові підказки, а не медичний діагноз. Кожну підозру слід "
                         "підтвердити з польотним лікарем."),
    "astro.edit": ("Edit metrics", "Редагувати показники"),
    "astro.game": ("Coordination test", "Тест на координацію"),
    "astro.history": ("History calendar", "Календар історії"),
    "astro.metrics_expander": ("Current metrics compared with your baseline",
                               "Поточні показники порівняно з вашою нормою"),
    "astro.engine_error": ("The diagnosis module is not available, so new metrics cannot be "
                           "assessed.",
                           "Модуль діагностики недоступний, тому нові показники неможливо оцінити."),

    "engine.title": ("The diagnosis engine is not set up yet",
                     "Модуль діагностики ще не налаштовано"),
    "engine.lead": ("Diagnoses are calculated by a small program written in C, and it has to be "
                    "compiled once on this computer. Until then you can still enter metrics, "
                    "browse the history, take the coordination test and log workouts.",
                    "Діагнози обчислює невелика програма мовою C, яку потрібно один раз "
                    "скомпілювати на цьому комп'ютері. Доти ви можете вносити показники, "
                    "переглядати історію, проходити тест на координацію та відмічати тренування."),
    "engine.reason_missing": ("The cause: no C compiler was found on this computer.",
                              "Причина: на цьому комп'ютері не знайдено компілятора C."),
    "engine.reason_failed": ("A C compiler was found, but the engine could not be built or "
                             "loaded. The details are at the bottom of this panel.",
                             "Компілятор C знайдено, але модуль не вдалося зібрати або "
                             "завантажити. Подробиці — внизу цієї панелі."),
    "engine.steps_heading": ("What to do on {os}", "Що робити в {os}"),
    "engine.os.windows": ("Windows", "Windows"),
    "engine.os.macos": ("macOS", "macOS"),
    "engine.os.linux": ("Linux", "Linux"),
    "engine.step_install.windows": ("Install the MinGW-w64 compiler. Run this in PowerShell:",
                                    "Встановіть компілятор MinGW-w64. Виконайте в PowerShell:"),
    "engine.step_install.macos": ("Install the Apple command line tools (a window will ask for "
                                  "confirmation):",
                                  "Встановіть інструменти командного рядка Apple (з'явиться "
                                  "вікно підтвердження):"),
    "engine.step_install.linux": ("Install the compiler (Debian and Ubuntu; other systems use "
                                  "their own package manager):",
                                  "Встановіть компілятор (Debian та Ubuntu; в інших системах — "
                                  "через їхній менеджер пакетів):"),
    "engine.step_restart.windows": ("Close the terminal and open a new one, so that it sees the "
                                    "compiler. Then go to the project folder and restart the app.",
                                    "Закрийте термінал і відкрийте новий, щоб він побачив "
                                    "компілятор. Потім перейдіть у папку проєкту й перезапустіть "
                                    "застосунок."),
    "engine.step_restart.macos": ("Open a new terminal window in the project folder.",
                                  "Відкрийте нове вікно терміналу в папці проєкту."),
    "engine.step_restart.linux": ("Open a new terminal in the project folder.",
                                  "Відкрийте новий термінал у папці проєкту."),
    "engine.step_check": ("Check that the compiler is found:",
                          "Перевірте, що компілятор знайдено:"),
    "engine.step_build": ("Build the engine from the project folder:",
                          "Зберіть модуль у папці проєкту:"),
    "engine.step_again": ("Press the button below. The app builds the engine itself and shows "
                          "your assessment.",
                          "Натисніть кнопку нижче. Застосунок сам збере модуль і покаже вашу "
                          "оцінку стану."),
    "engine.retry": ("Check again and build", "Перевірити ще раз і зібрати"),
    "engine.still_failing": ("Still not working. See the details below.",
                             "Досі не працює. Подробиці — нижче."),
    "engine.data_safe": ("Nothing is lost meanwhile: every entry you save is stored and gets its "
                         "diagnosis as soon as the engine is available.",
                         "Нічого не втрачається: кожен збережений запис зберігається й отримає "
                         "діагноз, щойно модуль стане доступним."),
    "engine.details": ("Technical details", "Технічні подробиці"),

    "severity.0": ("normal", "норма"),
    "severity.1": ("requires caution", "потребує обережності"),
    "severity.2": ("critical", "критично"),
    "body.figure_label": ("Body map with the zones that need attention",
                          "Мапа тіла із зонами, що потребують уваги"),
    "zone.head": ("Head and nervous system", "Голова та нервова система"),
    "zone.eyes": ("Eyes", "Очі"),
    "zone.neck": ("Neck vessels", "Судини шиї"),
    "zone.lungs": ("Lungs", "Легені"),
    "zone.heart": ("Heart and circulation", "Серце та кровообіг"),
    "zone.metabolism": ("Metabolism", "Обмін речовин"),
    "zone.immune": ("Immune system", "Імунна система"),
    "zone.bones": ("Bones", "Кістки"),
    "zone.muscles": ("Muscles", "М'язи"),
    "zone.whole_body": ("Whole body", "Увесь організм"),

    "table.metric": ("Metric", "Показник"),
    "table.current": ("Now", "Зараз"),
    "table.value": ("Value", "Значення"),
    "table.baseline": ("Baseline", "Норма"),
    "table.change": ("Change", "Зміна"),
    "table.recent": ("Recent median", "Медіана останніх записів"),
    "table.trend": ("Trend", "Тенденція"),
    "trend.up": ("rising", "зростає"),
    "trend.down": ("falling", "знижується"),
    "trend.flat": ("stable", "стабільно"),

    "workout.heading": ("Workouts", "Тренування"),
    "workout.reminder": ("Remember to do today's workout with the load determined for the "
                         "current stage of the flight according to the protocol.",
                         "Не забудьте виконати сьогоднішнє тренування з навантаженням, "
                         "визначеним для поточного етапу польоту згідно з протоколом."),
    "workout.stage": ("Current stage: {stage}.", "Поточний етап: {stage}."),
    "workout.done_button": ("Today's workout is done", "Сьогоднішнє тренування виконано"),
    "workout.none_button": ("No workout scheduled today", "Сьогодні тренування не заплановано"),
    "workout.done_status": ("Today's workout is recorded as done.",
                            "Сьогоднішнє тренування відмічено як виконане."),
    "workout.none_status": ("No workout is scheduled by the protocol for today.",
                            "На сьогодні тренування за протоколом не заплановано."),
    "workout.change": ("Change today's answer", "Змінити сьогоднішню відповідь"),
    "workout.legend_done": ("workout done", "тренування виконано"),
    "workout.legend_none": ("none scheduled", "не заплановано"),
    "workout.legend_today": ("today", "сьогодні"),
    "workout.month_total": ("Workouts done this month: {count}",
                            "Виконано тренувань цього місяця: {count}"),
    "workout.weekly_average": ("Average over the last 4 weeks: {value} a week",
                               "У середньому за останні 4 тижні: {value} на тиждень"),
    "calendar.previous": ("Previous month", "Попередній місяць"),
    "calendar.next": ("Next month", "Наступний місяць"),

    "edit.heading": ("Edit metrics", "Редагування показників"),
    "edit.intro": ("The form shows your current values. Change what you have measured and "
                   "save. Earlier entries stay in the history.",
                   "У формі — ваші поточні значення. Змініть те, що виміряли, і збережіть. "
                   "Попередні записи залишаються в історії."),
    "edit.save": ("Save metrics", "Зберегти показники"),
    "edit.cancel": ("Cancel", "Скасувати"),
    "edit.saved": ("Metrics saved at {when}.", "Показники збережено о {when}."),

    "history.heading": ("History calendar", "Календар історії"),
    "history.intro": ("Days with saved metrics are highlighted, with a line in the colour of "
                      "the most serious finding. Select a day to see every entry and diagnosis.",
                      "Дні зі збереженими показниками підсвічено, а лінія має колір "
                      "найсерйознішої підозри. Оберіть день, щоб побачити всі записи та діагнози."),
    "history.pick_day": ("Select a highlighted day to see its entries.",
                         "Оберіть підсвічений день, щоб переглянути його записи."),
    "history.empty_month": ("No metrics were saved in this month.",
                            "Цього місяця показники не зберігалися."),
    "history.entry_title": ("Metrics entered at {time}", "Показники внесено о {time}"),
    "history.source.baseline": ("Baseline measured on Earth", "Базові показники, виміряні на Землі"),
    "history.source.manual": ("Entered by hand", "Внесено вручну"),
    "history.source.game": ("Saved after the coordination test", "Збережено після тесту на координацію"),
    "history.environment": ("Environment: {env}", "Середовище: {env}"),
    "history.diagnosis_title": ("Diagnosis determined {when} for the environment “{env}”",
                                "Діагноз визначено {when} для середовища «{env}»"),
    "history.diagnosis_clear": ("No suspected pathologies.", "Підозр на патології немає."),
    "history.no_diagnosis": ("No diagnosis is stored for this entry.",
                             "Для цього запису діагноз не збережено."),
    "history.metrics_expander": ("All metrics of this entry", "Усі показники цього запису"),
    "history.changed_note": ("An asterisk marks values that differ from the previous entry.",
                             "Зірочкою позначено значення, що відрізняються від попереднього запису."),
    "history.export_heading": ("Export for the doctor", "Експорт для лікаря"),
    "history.export_note": ("CSV files open in Excel and other spreadsheet programs. They contain "
                            "every entry and every diagnosis ever saved for this profile.",
                            "CSV-файли відкриваються в Excel та інших табличних програмах. Вони "
                            "містять усі записи й усі діагнози, збережені для цього профілю."),
    "history.export_metrics": ("Download metrics (CSV)", "Завантажити показники (CSV)"),
    "history.export_diagnoses": ("Download diagnoses (CSV)", "Завантажити діагнози (CSV)"),
    "history.export_nothing": ("Nothing to export yet.", "Поки що нічого експортувати."),
    "history.back": ("Back to profile", "Назад до профілю"),

    "game.heading": ("Coordination test", "Тест на координацію"),
    "game.intro": ("A small spaceship flies across the field and keeps changing direction. "
                   "Keep the cursor on it for as long as you can. The test takes {seconds} "
                   "seconds, and the result is the share of that time you stayed on the ship.",
                   "Невеликий космічний корабель літає полем і постійно змінює напрямок. "
                   "Утримуйте на ньому курсор якомога довше. Тест триває {seconds} секунд, а "
                   "результат — це частка часу, протягом якого курсор був на кораблі."),
    "game.result": ("Result: {score}%", "Результат: {score} %"),
    "game.details": ("On the ship for {on} s of {total} s. Longest unbroken hold: {hold} s.",
                     "На кораблі {on} с із {total} с. Найдовше безперервне утримання: {hold} с."),
    "game.baseline": ("Your baseline is {baseline}%.", "Ваша норма — {baseline} %."),
    "game.save": ("Save result to metrics", "Зберегти результат у показники"),
    "game.saved": ("Coordination result {score}% saved to your metrics.",
                   "Результат координації {score} % збережено у ваших показниках."),
    "game.back": ("Back to profile", "Назад до профілю"),
    "game.error": ("The test result could not be read. Run the test again.",
                   "Не вдалося прочитати результат тесту. Пройдіть тест ще раз."),
    "game.progress_heading": ("Progress across tests", "Динаміка результатів тестів"),
    "game.progress_empty": ("Save at least two test results to see a trend here.",
                            "Збережіть щонайменше два результати тесту, щоб побачити тут динаміку."),
    "game.progress_summary": (
        "Tests saved: {count}. Best: {best}%. Latest: {latest}%. Average of the last tests: "
        "{last}% (first tests: {first}%, change {change} points).",
        "Збережено тестів: {count}. Найкращий: {best} %. Останній: {latest} %. Середнє за "
        "останні тести: {last} % (за перші: {first} %, зміна {change} пункту)."),
    "game.series.score": ("Test result", "Результат тесту"),
    "game.series.average": ("Average of the last 3 tests", "Середнє за останні 3 тести"),
    "game.series.baseline": ("Earth baseline", "Норма на Землі"),
    "game.js.start": ("Start test", "Почати тест"),
    "game.js.again": ("Run again", "Пройти ще раз"),
    "game.js.ready": ("Put the cursor on the ship and press the button.",
                      "Наведіть курсор на корабель і натисніть кнопку."),
    "game.js.get_ready": ("Get ready", "Приготуйтеся"),
    "game.js.time": ("Time left", "Залишилось"),
    "game.js.on_target": ("On the ship", "На кораблі"),
    "game.js.finished": ("Test finished", "Тест завершено"),
    "game.js.seconds": ("s", "с"),
}

MONTHS = {
    "en": ("January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"),
    "uk": ("Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень",
           "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"),
}
MONTHS_IN_DATES = {
    "en": MONTHS["en"],
    "uk": ("січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня",
           "вересня", "жовтня", "листопада", "грудня"),
}
WEEKDAYS = {
    "en": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
    "uk": ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"),
}
DATE_INPUT_FORMATS = {"en": "YYYY-MM-DD", "uk": "DD.MM.YYYY"}


def language() -> str:
    chosen = st.session_state.get("lang", DEFAULT_LANGUAGE)
    return chosen if chosen in LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, **values: Any) -> str:
    pair = TEXTS.get(key)
    if pair is None:
        return key
    text = pair[LANGUAGES.index(language())]
    return text.format(**values) if values else text


def month_title(year: int, month: int) -> str:
    return f"{MONTHS[language()][month - 1]} {year}"


def weekdays() -> tuple[str, ...]:
    return WEEKDAYS[language()]


def date_input_format() -> str:
    return DATE_INPUT_FORMATS[language()]


def format_date(day: date) -> str:
    return f"{day.day} {MONTHS_IN_DATES[language()][day.month - 1]} {day.year}"


def format_time(moment: datetime, seconds: bool = False) -> str:
    return moment.strftime("%H:%M:%S" if seconds else "%H:%M")


def format_datetime(moment: datetime) -> str:
    return f"{format_date(moment)}, {format_time(moment)}"


def format_number(value: float, decimals: int = 0) -> str:
    text = f"{value:.{decimals}f}"
    return text.replace(".", ",") if language() == "uk" else text


def metric_decimals(metric: catalog.Metric) -> int:
    if metric.integer:
        return 0
    step = f"{metric.step:.10f}".rstrip("0")
    return len(step.split(".")[1]) if "." in step else 0


def unit_label(unit: str) -> str:
    return t(f"unit.{unit}") if unit else ""


def input_label(key: str) -> str:
    question = f"question.{key}"
    return t(question) if question in TEXTS else t(f"metric.{key}")


def metric_label(key: str, with_unit: bool = False, unit: str | None = None) -> str:
    label = t(f"metric.{key}")
    metric = catalog.BY_KEY[key]
    shown_unit = unit or metric.unit
    if with_unit and metric.kind == catalog.NUMBER and shown_unit:
        return f"{label}, {unit_label(shown_unit)}"
    return label


def format_metric(key: str, value: Any) -> str:
    if catalog.is_missing(value):
        return "—"
    metric = catalog.BY_KEY[key]
    if metric.kind in (catalog.CHOICE, catalog.FLAG):
        return t(f"option.{key}.{int(value)}")
    if metric.kind == catalog.SCORE:
        whole = float(value) == int(value)
        score = format_number(float(value), 0 if whole else 1)
        return f"{score} {unit_label(metric.unit)}"
    number = format_number(float(value), metric_decimals(metric))
    unit = unit_label(metric.unit)
    if metric.unit == "pct":
        return f"{number}%" if language() == "en" else f"{number} %"
    return f"{number} {unit}" if unit else number


def format_change(key: str, change: Any) -> str:
    if catalog.is_missing(change):
        return ""
    metric = catalog.BY_KEY[key]
    decimals = metric_decimals(metric)
    if round(float(change), decimals) == 0:
        return "0"
    sign = "+" if change > 0 else "−"
    return f"{sign}{format_number(abs(float(change)), decimals)}"
