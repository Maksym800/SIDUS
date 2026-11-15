from __future__ import annotations

from dataclasses import dataclass

LANGUAGES = ("en", "uk")


@dataclass(frozen=True)
class Description:
    name: str
    explanation: str
    advice: str


@dataclass(frozen=True)
class _Entry:
    metrics: tuple[str, ...]
    en: Description
    uk: Description


def _entry(metrics, en, uk) -> _Entry:
    return _Entry(tuple(metrics), Description(*en), Description(*uk))


_ENTRIES: dict[str, _Entry] = {
    "TACHYCARDIA": _entry(
        ["heart_rate_bpm"],
        ("Suspected tachycardia",
         "Your resting heart rate is well above your Earth baseline. Dehydration, stress, "
         "a raised temperature, cardiovascular deconditioning and recent exertion are the "
         "usual causes.",
         "Rest for 10 minutes and measure again. Drink water. If the pulse stays high or "
         "you feel palpitations or chest discomfort, contact the flight surgeon."),
        ("Підозра на тахікардію",
         "Частота серцевих скорочень у спокої помітно вища за вашу земну норму. Найчастіші "
         "причини — зневоднення, стрес, підвищена температура, детренованість "
         "серцево-судинної системи або нещодавнє навантаження.",
         "Відпочиньте 10 хвилин і виміряйте пульс ще раз. Випийте води. Якщо пульс "
         "залишається високим або ви відчуваєте серцебиття чи дискомфорт у грудях, "
         "зверніться до польотного лікаря."),
    ),
    "BRADYCARDIA": _entry(
        ["heart_rate_bpm"],
        ("Suspected bradycardia",
         "Your resting heart rate is unusually low compared with your baseline. It can "
         "reflect strong vagal tone, a medication effect, low body temperature or a problem "
         "with the heart's conduction system.",
         "Measure again. If you feel dizzy, weak or close to fainting, report it straight "
         "away and record an ECG."),
        ("Підозра на брадикардію",
         "Частота серцевих скорочень у спокої незвично низька порівняно з вашою нормою. "
         "Причиною можуть бути підвищений тонус блукаючого нерва, дія ліків, "
         "переохолодження або порушення провідності серця.",
         "Повторіть вимірювання. Якщо є запаморочення, слабкість чи переднепритомний стан, "
         "негайно повідомте про це і запишіть ЕКГ."),
    ),
    "HYPERTENSION": _entry(
        ["bp_systolic", "bp_diastolic"],
        ("Suspected arterial hypertension",
         "Your blood pressure is above the normal range or well above your baseline. "
         "Stress, salty food, poor sleep and the shift of body fluids towards the head can "
         "all raise it.",
         "Sit calmly for 5 minutes and repeat the measurement on the same arm. Cut down on "
         "salt and check your sleep and stress. Readings that stay high need a medical "
         "consultation."),
        ("Підозра на артеріальну гіпертензію",
         "Артеріальний тиск вищий за норму або значно вищий за ваш базовий рівень. Його "
         "можуть підвищувати стрес, солона їжа, нестача сну та перерозподіл рідини до "
         "голови.",
         "Спокійно посидьте 5 хвилин і повторіть вимірювання на тій самій руці. Обмежте "
         "сіль, зверніть увагу на сон і рівень стресу. Якщо тиск залишається високим, "
         "потрібна консультація лікаря."),
    ),
    "HYPOTENSION": _entry(
        ["bp_systolic", "bp_diastolic"],
        ("Suspected arterial hypotension",
         "Your blood pressure is below the normal range or well below your baseline. In "
         "flight this usually comes from fluid loss and cardiovascular deconditioning, and "
         "it raises the risk of fainting when gravity returns.",
         "Drink fluids with electrolytes, avoid sudden changes of posture and measure "
         "again. Report dizziness or darkening of vision."),
        ("Підозра на артеріальну гіпотензію",
         "Артеріальний тиск нижчий за норму або значно нижчий за ваш базовий рівень. У "
         "польоті це зазвичай пов'язано з втратою рідини та детренованістю "
         "серцево-судинної системи і підвищує ризик непритомності після повернення "
         "гравітації.",
         "Пийте рідину з електролітами, уникайте різких змін положення тіла і повторіть "
         "вимірювання. Повідомте про запаморочення чи потемніння в очах."),
    ),
    "ARRHYTHMIA": _entry(
        ["ecg_rhythm"],
        ("Suspected arrhythmia",
         "The ECG shows an irregular heart rhythm. Shifts in electrolytes, stress hormones "
         "and fatigue can provoke rhythm disturbances during spaceflight.",
         "Record a full ECG and send it to the medical team. Avoid heavy exertion until it "
         "has been reviewed. Chest pain, breathlessness or fainting need help at once."),
        ("Підозра на аритмію",
         "ЕКГ показує нерегулярний серцевий ритм. Під час космічного польоту порушення "
         "ритму можуть провокувати зміни балансу електролітів, гормони стресу та втома.",
         "Запишіть повну ЕКГ і передайте її медичній групі. До отримання висновку уникайте "
         "важких навантажень. Біль у грудях, задишка чи непритомність потребують негайної "
         "допомоги."),
    ),
    "LOW_HRV": _entry(
        ["hrv_rmssd_ms"],
        ("Suspected autonomic strain (reduced heart-rate variability)",
         "Your heart-rate variability has fallen well below your baseline. That points to "
         "dominant stress activation and incomplete recovery.",
         "Put sleep and recovery first, lower the training intensity for a day and watch "
         "HRV in the next entries."),
        ("Підозра на вегетативне перенапруження (знижена варіабельність серцевого ритму)",
         "Варіабельність серцевого ритму значно знизилася порівняно з вашою нормою. Це "
         "вказує на переважання стресової активації та неповне відновлення.",
         "Насамперед подбайте про сон і відновлення, на день знизьте інтенсивність "
         "тренувань і стежте за ВСР у наступних записах."),
    ),
    "VENOUS_CONGESTION": _entry(
        ["blood_flow_cm_s", "vascular_condition"],
        ("Suspected venous congestion with a risk of thrombosis",
         "Blood flow in the neck veins is slowed or abnormal. Without gravity blood shifts "
         "towards the head, flow in the jugular vein can stagnate or reverse, and a clot "
         "has been found this way in an astronaut on orbit.",
         "Repeat the ultrasound scan of the jugular vein and send the images to the "
         "medical team. Do not massage the neck. Report neck swelling, pain or headache "
         "urgently."),
        ("Підозра на венозний застій із ризиком тромбозу",
         "Кровотік у венах шиї сповільнений або порушений. Без гравітації кров зміщується "
         "до голови, течія в яремній вені може застоюватися або ставати зворотною; саме "
         "так в астронавта на орбіті було виявлено тромб.",
         "Повторіть УЗД яремної вени та передайте знімки медичній групі. Не масажуйте шию. "
         "Про набряк шиї, біль або головний біль повідомляйте терміново."),
    ),
    "SANS": _entry(
        ["vision_clear", "vascular_condition", "blood_flow_cm_s"],
        ("Suspected spaceflight-associated neuro-ocular syndrome (SANS)",
         "Your vision is no longer sharp. In reduced gravity body fluids shift towards the "
         "head, which can swell the optic disc, flatten the back of the eye and change "
         "focus.",
         "Run the on-board eye checks (acuity chart, Amsler grid, and OCT or fundoscopy if "
         "available) and report the results. Use your adjustable-focus glasses if they "
         "were issued."),
        ("Підозра на нейроокулярний синдром, пов'язаний із космічним польотом (SANS)",
         "Зір втратив гостроту. За зниженої гравітації рідина в організмі зміщується до "
         "голови, що може спричинити набряк диска зорового нерва, сплощення задньої "
         "частини ока та зміну фокусування.",
         "Виконайте бортові перевірки зору (таблиця гостроти зору, сітка Амслера, за "
         "наявності — ОКТ або офтальмоскопія) і повідомте результати. Користуйтеся "
         "окулярами з регульованим фокусом, якщо їх видано."),
    ),
    "VISUAL_IMPAIRMENT": _entry(
        ["vision_clear"],
        ("Suspected visual impairment",
         "You reported that your vision is not sharp or clear. On Earth the usual causes "
         "are eye strain, dry eyes, a change in refraction or tiredness.",
         "Rest your eyes and check again after sleep. See an eye doctor if the blur stays "
         "or if it appeared suddenly."),
        ("Підозра на порушення зору",
         "Ви зазначили, що зір не гострий або нечіткий. На Землі найчастіші причини — "
         "перенапруження очей, сухість, зміна рефракції або втома.",
         "Дайте очам відпочити й перевірте зір після сну. Зверніться до офтальмолога, якщо "
         "нечіткість не минає або з'явилася раптово."),
    ),
    "SLEEP_DISORDER": _entry(
        ["sleep_hours", "sleep_efficiency_pct"],
        ("Suspected sleep disorder (sleep deprivation)",
         "Your sleep is too short or too broken. In flight the usual causes are a shifted "
         "day–night cycle, noise, workload and stress, and missing sleep quickly lowers "
         "attention and reaction speed.",
         "Keep fixed times for going to sleep and waking up, dim the lights and put "
         "screens away before sleep, and avoid caffeine in the second half of the day. "
         "Tell the flight surgeon if it lasts several days."),
        ("Підозра на порушення сну (дефіцит сну)",
         "Сон надто короткий або переривчастий. У польоті звичні причини — зміщений "
         "добовий ритм, шум, робоче навантаження та стрес; нестача сну швидко знижує "
         "увагу та швидкість реакції.",
         "Лягайте і прокидайтеся в один і той самий час, перед сном приглушуйте світло й "
         "відкладайте екрани, не вживайте кофеїн у другій половині дня. Якщо проблема "
         "триває кілька днів, повідомте польотного лікаря."),
    ),
    "MUSCLE_ATROPHY": _entry(
        ["muscle_thickness_mm", "muscle_structure"],
        ("Suspected muscle atrophy",
         "Muscle thickness has decreased against your baseline, or the ultrasound shows a "
         "change in muscle structure. Without load the leg and back muscles lose mass and "
         "strength quickly.",
         "Do every resistance session in the protocol, check your protein intake and "
         "repeat the scan at the next planned check."),
        ("Підозра на м'язову атрофію",
         "Товщина м'яза зменшилася порівняно з вашою нормою або УЗД показує зміни його "
         "структури. Без навантаження м'язи ніг і спини швидко втрачають масу та силу.",
         "Виконуйте всі силові тренування за протоколом, перевірте споживання білка і "
         "повторіть УЗД під час наступного планового огляду."),
    ),
    "FEVER": _entry(
        ["body_temp_c"],
        ("Suspected fever (infection or overheating)",
         "Your body temperature is raised. Infection, inflammation and heat built up "
         "during exercise are the usual causes; without gravity the body sheds heat less "
         "efficiently.",
         "Measure again after 30 minutes of rest, drink fluids and check for other "
         "symptoms such as a sore throat, cough or pain. Report a temperature of 38 °C or "
         "higher."),
        ("Підозра на гарячку (інфекція або перегрівання)",
         "Температура тіла підвищена. Найчастіші причини — інфекція, запалення або "
         "перегрівання під час тренування; без гравітації організм гірше віддає тепло.",
         "Виміряйте температуру ще раз після 30 хвилин відпочинку, пийте рідину й "
         "перевірте, чи немає інших симптомів — болю в горлі, кашлю, болю. Про "
         "температуру 38 °C і вище повідомте лікаря."),
    ),
    "HYPOTHERMIA": _entry(
        ["body_temp_c"],
        ("Suspected hypothermia",
         "Your body temperature is below normal. Check the cabin or suit thermal control "
         "first, and the thermometer second.",
         "Add clothing layers, have a warm drink and measure again in 20–30 minutes. "
         "Report shivering, confusion or drowsiness."),
        ("Підозра на гіпотермію (переохолодження)",
         "Температура тіла нижча за норму. Спершу перевірте систему терморегулювання "
         "кабіни чи скафандра, а потім — термометр.",
         "Одягніться тепліше, випийте теплий напій і повторіть вимірювання через 20–30 "
         "хвилин. Повідомте про тремтіння, сплутаність свідомості чи сонливість."),
    ),
    "HYPOXEMIA": _entry(
        ["spo2_pct"],
        ("Suspected hypoxemia",
         "Your blood oxygen saturation is below normal. The cause can be the cabin or suit "
         "atmosphere, a breathing problem, or a sensor that sits badly on the finger.",
         "Put the sensor on a warm finger and measure again. If the value stays low, check "
         "the cabin atmosphere (O₂ and CO₂), stop any exertion and report at once. Below "
         "90 % is an emergency."),
        ("Підозра на гіпоксемію",
         "Насичення крові киснем нижче за норму. Причиною може бути склад атмосфери "
         "кабіни чи скафандра, порушення дихання або погано закріплений датчик.",
         "Одягніть датчик на теплий палець і повторіть вимірювання. Якщо показник "
         "залишається низьким, перевірте атмосферу кабіни (O₂ і CO₂), припиніть "
         "навантаження і негайно повідомте. Значення нижче 90 % — невідкладний стан."),
    ),
    "SENSORIMOTOR": _entry(
        ["coordination_pct"],
        ("Suspected sensorimotor impairment",
         "Your hand–eye coordination and reaction speed are worse than your baseline. This "
         "is typical while adapting to a new gravity level, and also with fatigue, poor "
         "sleep or raised CO₂.",
         "If you can, postpone tasks that need fine control (piloting, robotic arm work, "
         "spacewalks), rest and repeat the test."),
        ("Підозра на сенсомоторні порушення",
         "Координація «рука–око» та швидкість реакції гірші за вашу норму. Це типово під "
         "час адаптації до нового рівня гравітації, а також за втоми, нестачі сну чи "
         "підвищеного рівня CO₂.",
         "За можливості відкладіть завдання, що потребують точних рухів (пілотування, "
         "робота з маніпулятором, вихід у відкритий космос), відпочиньте й повторіть тест."),
    ),
    "HYPOGLYCEMIA": _entry(
        ["glucose_mmol_l"],
        ("Suspected hypoglycemia",
         "Your blood glucose is below normal. Missed meals, hard exercise and an energy "
         "deficit are the usual causes.",
         "Take fast carbohydrates now (juice or glucose tablets) and measure again in 15 "
         "minutes. Do not start demanding tasks until the value is back to normal."),
        ("Підозра на гіпоглікемію",
         "Рівень глюкози в крові нижчий за норму. Звичні причини — пропущений прийом їжі, "
         "інтенсивне тренування або дефіцит енергії.",
         "Одразу прийміть швидкі вуглеводи (сік або таблетки глюкози) і повторіть "
         "вимірювання через 15 хвилин. Не беріться за відповідальні завдання, доки "
         "показник не нормалізується."),
    ),
    "HYPERGLYCEMIA": _entry(
        ["glucose_mmol_l"],
        ("Suspected hyperglycemia",
         "Your blood glucose is above normal. Long stays without gravity can reduce "
         "insulin sensitivity, and stress hormones or a recent meal raise glucose too.",
         "Measure again fasting, at least 8 hours after food. Drink water and keep to the "
         "exercise plan. Report repeated high values."),
        ("Підозра на гіперглікемію",
         "Рівень глюкози в крові вищий за норму. Тривале перебування без гравітації може "
         "знижувати чутливість до інсуліну; глюкозу підвищують також гормони стресу та "
         "нещодавній прийом їжі.",
         "Повторіть вимірювання натще, щонайменше через 8 годин після їжі. Пийте воду й "
         "дотримуйтеся плану тренувань. Про повторні високі значення повідомте лікаря."),
    ),
    "STRESS_IMMUNE": _entry(
        ["cortisol_nmol_l"],
        ("Suspected stress-related weakening of the immune response",
         "Your cortisol is well above your baseline. Stress hormones that stay high "
         "suppress immune cells and make infections and reactivation of dormant viruses "
         "more likely.",
         "Reduce the workload where you can, protect your sleep and use your relaxation "
         "routine. Repeat the cortisol test at the same time of day."),
        ("Підозра на стрес-зумовлене ослаблення імунної відповіді",
         "Рівень кортизолу значно перевищує вашу норму. Тривало підвищені гормони стресу "
         "пригнічують імунні клітини й підвищують імовірність інфекцій та реактивації "
         "латентних вірусів.",
         "За можливості зменште робоче навантаження, подбайте про сон і застосовуйте "
         "звичні техніки релаксації. Повторіть тест на кортизол у той самий час доби."),
    ),
    "VIRAL_REACTIVATION": _entry(
        ["viral_activation", "body_temp_c"],
        ("Suspected reactivation of latent viruses",
         "Signs of viral activation were noticed. Dormant herpesviruses (EBV, VZV, CMV, "
         "HSV-1) reactivate in more than half of crew members during flight, when stress "
         "weakens immune control.",
         "Report it to the flight surgeon and watch for a rash, fever or pain. Keep to the "
         "hygiene rules and do not share utensils, to protect your crewmates."),
        ("Підозра на реактивацію латентних вірусів",
         "Помічено ознаки активації вірусів. Латентні герпесвіруси (вірус Епштейна — Барр, "
         "вірус вітряної віспи, цитомегаловірус, вірус простого герпесу 1-го типу) "
         "реактивуються під час польоту більш ніж у половини членів екіпажу, коли стрес "
         "послаблює імунний контроль.",
         "Повідомте польотного лікаря і стежте, чи не з'являються висип, гарячка або біль. "
         "Дотримуйтеся правил гігієни й не користуйтеся спільним посудом, щоб захистити "
         "інших членів екіпажу."),
    ),
    "BONE_LOSS": _entry(
        ["bone_resorption_ntx"],
        ("Suspected accelerated bone loss",
         "The bone-resorption marker has risen well above your baseline: bone is being "
         "broken down faster than it is rebuilt. Without load, weight-bearing bones lose "
         "about 1–1.5 % of their mineral density a month.",
         "Do not skip resistance and treadmill sessions, check your calcium and vitamin D "
         "intake and discuss countermeasures with the medical team."),
        ("Підозра на прискорену втрату кісткової маси",
         "Маркер резорбції кістки значно перевищив вашу норму: кісткова тканина руйнується "
         "швидше, ніж відновлюється. Без навантаження опорні кістки втрачають приблизно "
         "1–1,5 % мінеральної щільності на місяць.",
         "Не пропускайте силові тренування та заняття на біговій доріжці, перевірте "
         "споживання кальцію та вітаміну D й обговоріть профілактичні заходи з медичною "
         "групою."),
    ),
    "HYPERCALCEMIA": _entry(
        ["calcium_mmol_l"],
        ("Suspected hypercalcemia (risk of kidney stones)",
         "Your blood calcium is above normal. In flight, calcium released from bone raises "
         "the load on the kidneys and the risk of stones.",
         "Drink more water (2–3 litres a day), limit salt and repeat the test."),
        ("Підозра на гіперкальціємію (ризик каменів у нирках)",
         "Рівень кальцію в крові вищий за норму. У польоті кальцій, що вивільняється з "
         "кісток, підвищує навантаження на нирки та ризик утворення каменів.",
         "Пийте більше води (2–3 літри на добу), обмежте сіль і повторіть аналіз."),
    ),
    "HYPOCALCEMIA": _entry(
        ["calcium_mmol_l"],
        ("Suspected hypocalcemia",
         "Your blood calcium is below normal. Low calcium intake or a lack of vitamin D "
         "are the usual causes; cramps, tingling and rhythm disturbances can follow.",
         "Review your diet and vitamin D supplement, report cramps or numbness and repeat "
         "the test."),
        ("Підозра на гіпокальціємію",
         "Рівень кальцію в крові нижчий за норму. Звичні причини — недостатнє споживання "
         "кальцію або нестача вітаміну D; можливі судоми, поколювання та порушення "
         "серцевого ритму.",
         "Перегляньте раціон і прийом вітаміну D, повідомте про судоми чи оніміння і "
         "повторіть аналіз."),
    ),
    "PSYCH_STRAIN": _entry(
        ["mood_score", "stress_score"],
        ("Suspected psycho-emotional strain",
         "Your mood is low or your stress level is high. Isolation, confinement, a heavy "
         "workload and distance from family are well-known stressors on long missions.",
         "Plan time for rest and for yourself, talk to family or friends, and keep "
         "exercising. Ask for a private psychological conference if it does not pass."),
        ("Підозра на психоемоційне перенапруження",
         "Настрій знижений або рівень стресу високий. Ізоляція, замкнений простір, велике "
         "робоче навантаження та віддаленість від рідних — відомі стресові чинники "
         "тривалих місій.",
         "Заплануйте час на відпочинок і на себе, поговоріть із рідними чи друзями, не "
         "припиняйте тренувань. Якщо стан не минає, попросіть про приватну психологічну "
         "консультацію."),
    ),
    "RADIATION_DOSE": _entry(
        ["radiation_total_msv"],
        ("Suspected excessive radiation exposure",
         "Your accumulated dose is approaching or exceeding the 600 mSv career limit, or "
         "it is growing faster than this environment explains.",
         "Report your dosimeter readings to mission control, spend more time in the "
         "best-shielded areas and review the exposure plan for the rest of the mission."),
        ("Підозра на надмірне радіаційне опромінення",
         "Накопичена доза наближається до кар'єрного ліміту 600 мЗв чи перевищує його або "
         "зростає швидше, ніж можна пояснити умовами цього середовища.",
         "Передайте показники дозиметра до центру керування польотом, більше часу "
         "проводьте в найкраще захищених відсіках і перегляньте план опромінення на решту "
         "місії."),
    ),
    "RADIATION_RATE": _entry(
        ["neutron_rate_usv_h"],
        ("Suspected acute radiation hazard (high neutron dose rate)",
         "The neutron dose rate is above the level expected for this environment. It can "
         "mean a solar particle event, a weakly shielded spot or a faulty dosimeter.",
         "Move to the storm shelter or the best-shielded module, check a second dosimeter "
         "and notify mission control."),
        ("Підозра на гостру радіаційну небезпеку (висока потужність дози нейтронів)",
         "Потужність дози нейтронного випромінювання перевищує рівень, очікуваний для "
         "цього середовища. Це може означати сонячну протонну подію, слабко захищене "
         "місце або несправність дозиметра.",
         "Перейдіть до радіаційного сховища або найкраще захищеного модуля, звірте "
         "показники з другим дозиметром і повідомте центр керування польотом."),
    ),
    "MASS_LOSS": _entry(
        ["mass_kg"],
        ("Suspected energy deficit (body mass loss)",
         "Your body mass has dropped against your baseline. In flight appetite falls while "
         "exercise burns a lot of energy, and losing mass speeds up the loss of muscle and "
         "bone.",
         "Log what you eat, add calories and fluids and weigh yourself again under the "
         "same conditions."),
        ("Підозра на енергетичний дефіцит (втрата маси тіла)",
         "Маса тіла знизилася порівняно з вашою нормою. У польоті апетит зменшується, а "
         "тренування потребують багато енергії; втрата маси прискорює втрату м'язів і "
         "кісткової тканини.",
         "Ведіть облік з'їденого, додайте калорій і рідини та зважтеся повторно за тих "
         "самих умов."),
    ),
}

CODES: tuple[str, ...] = tuple(_ENTRIES)


def describe(code: str, language: str) -> Description:
    entry = _ENTRIES[code]
    return entry.uk if language == "uk" else entry.en


def related_metrics(code: str) -> tuple[str, ...]:
    return _ENTRIES[code].metrics
