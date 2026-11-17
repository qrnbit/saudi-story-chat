# خطوات التشغيل

## 1) مفتاح OpenRouter
1. سجّل في https://openrouter.ai
2. ادخل Keys ← Create Key، وانسخ المفتاح (يبدأ بـ sk-or-).
3. الموديل الافتراضي `cognitivecomputations/dolphin-mistral-24b-venice-edition` مدفوع (رخيص جداً، تقريباً 0.20 دولار لكل مليون توكن)، فلازم يكون عندك رصيد في الحساب من Credits. لو تبي تبدأ مجاناً، حط `MODEL_ID` على موديل مجاني مثل `google/gemma-4-31b-it:free`.

## 2) قبل التشغيل: تأكد من الموديل
**قبل التشغيل، تأكد إن MODEL_ID موجود في https://openrouter.ai/models وإنه لسا مجاني، لأن القائمة تتغير.**
(وإذا كان موديل مدفوع، تأكد إن عندك رصيد.)

## 3) إنشاء الـ Space
1. سجّل في https://huggingface.co ثم New ← Space.
2. اختر اسم، و SDK = **Docker** (Blank)، و Hardware = CPU basic (مجاني)، والخصوصية Public (عشان UptimeRobot يقدر يوصل لـ /health).
3. اضغط Create Space.

## 4) رفع الملفات
من تبويب Files ← Add file ← Upload files، ارفع:
`app.py`, `config.py`, `system_prompt.txt`, `requirements.txt`, `Dockerfile`, `README.md`, ومجلد `static/` (فيه `index.html`).
ملاحظة: استبدل README.md الافتراضي بالموجود هنا لأن أوله إعدادات الـ Space.

## 5) إضافة الأسرار (إلزامية)
Settings ← Variables and secrets:
- **New secret**: الاسم `OPENROUTER_API_KEY` والقيمة مفتاحك (إلزامي لو `PROVIDER` = `openrouter` أو `openrouter_free`).
- **New secret**: الاسم `APP_PASSWORD` وكلمة مرور قوية. **إلزامي**: إذا ما حطيته، السيرفر يرفض يشتغل ويطلع خطأ في الـ Logs.
- (اختياري) **New variable**: `MODEL_ID` لو تبي تغيّر الموديل بدون تعديل الكود.
بعد أي تعديل، الـ Space يعيد التشغيل تلقائياً.

كلمة المرور (الرمز السري) ما تنحفظ في الكود ولا في الصفحة. أول ما تفتح الموقع تطلع لك شاشة قفل بأرقام مثل الآيفون، وكل محاولة يتحقق منها السيرفر عن طريق `/auth`. وبطلبك: لازم تدخل الرمز الصحيح 4 مرات، أول 3 مرات يقول "الرمز غلط" والرابعة يفتح، والرمز الغلط ما ينحسب. بعد ما يفتح ينحفظ الرمز لين تقفل التبويب (sessionStorage)، ويرجع القفل إذا رد السيرفر 401 أو ضغطت زر القفل 🔒.

## 6) التجربة
رابط تطبيقك المباشر يكون: `https://USERNAME-SPACENAME.hf.space`
- افتحه، أدخل كلمة المرور، وجرب الدردشة.
- افتح `https://USERNAME-SPACENAME.hf.space/health` ولازم يطلع `OK`.
- إذا ما اشتغل، شوف تبويب Logs في الـ Space.

## 7) UptimeRobot
1. سجّل في https://uptimerobot.com (مجاني).
2. Add New Monitor ← النوع HTTP(s).
3. URL: `https://USERNAME-SPACENAME.hf.space/health`
4. Interval: **5 minutes** ← Create.

الحد الأدنى للفاصل في الخطة المجانية هو **5 دقائق** (مو 4)، وهذا كافي لإبقاء الـ Space صاحي، لأن الـ Space المجاني ما ينام إلا بعد 48 ساعة بدون نشاط.

## ⚠️ حدود OpenRouter
- الخطة المجانية في OpenRouter تعطي تقريباً **50 طلب باليوم** على الموديلات المجانية (`:free`).
- الاستخدام المكثف لكتابة القصص الطويلة قد يحتاج تشحن **10 دولار** (مرة وحدة) عشان يرتفع الحد إلى **1000 طلب يومياً**.
- الموديلات المدفوعة (مثل الافتراضي) تنخصم من رصيدك حسب الاستخدام.
- تقدر تتأكد من الحدود الحالية هنا: https://openrouter.ai/docs/api-reference/limits

## حماية إضافية
- `/chat` محدود بـ **20 طلب بالدقيقة لكل IP**، وإذا زاد يرجع خطأ 429 والواجهة تقول "استنى دقيقة".
- كل طلب لازم يكون معه كلمة المرور في هيدر `X-App-Password`، وإلا يرجع 401.

## المزودين (PROVIDER)
من Settings ← Variables and secrets ← New variable (أو عدّل الموجود) باسم `PROVIDER`. القيم المتاحة:

| القيمة | وش يسوي | يحتاج |
|---|---|---|
| `openrouter` (الافتراضي) | OpenRouter مع `MODEL_ID` | مفتاح OpenRouter، ورصيد لو الموديل مدفوع |
| `openrouter_free` | OpenRouter مع قائمة موديلات مجانية `FREE_MODEL_IDS`، يجربها بالترتيب | مفتاح OpenRouter بس، بدون رصيد |
| `pollinations` | Pollinations.ai مجاناً | ولا شي، بدون مفتاح |

1. **للاستخدام المجاني غير المحدود: غيّر PROVIDER إلى pollinations في إعدادات الـ Space.**
2. **للعودة لـ OpenRouter: غيّرها إلى openrouter.**
3. **لموديلات OpenRouter المجانية: غيّرها إلى openrouter_free، وحط أسماء الموديلات في متغير `FREE_MODEL_IDS` مفصولة بفواصل.**

### قائمة الموديلات المجانية (FREE_MODEL_IDS)
- الكود يجرب أول موديل في القائمة. إذا فشل (429، أو خطأ، أو الموديل مو موجود، أو رد فاضي)، ينتقل للي بعده، وهكذا للآخر.
- إذا فشلت كلها، ينتقل تلقائياً لـ Pollinations (لو الـ Fallback مفعّل).
- القيمة الافتراضية:
  ```
  google/gemma-4-31b-it:free,nousresearch/hermes-3-llama-3.1-405b:free
  ```
- لتغييرها: أضف Variable اسمه `FREE_MODEL_IDS` وحط الأسماء مفصولة بفواصل، بدون مسافات أو معها (الكود يشيل المسافات). مثال:
  ```
  google/gemma-4-31b-it:free,google/gemma-4-26b-a4b-it:free,nvidia/nemotron-3-ultra-550b-a55b:free
  ```
- رتّبها من الأفضل للأقل، لأن الأول هو اللي ينستخدم أغلب الوقت.
- ⚠️ `nousresearch/hermes-3-llama-3.1-405b:free` ما كان موجود في OpenRouter يوم 17 نوفمبر 2026 (المتاح بس `nousresearch/hermes-4-405b` وهو مدفوع). وجوده في القائمة ما يضر، الكود بس يتخطاه للي بعده، لكن الأفضل تستبدله بموديل متاح من الجدول تحت.

الـ Space يعيد التشغيل تلقائياً بعد التغيير، وأعلى الصفحة يوضح المزود والموديل الشغالين.

## الانتقال التلقائي لـ Pollinations (Fallback)
- مفعّل افتراضياً: لو المزود الأساسي فشل (429 تجاوز الحد، أو خطأ في السيرفر، أو انتهى الوقت، أو رجع رد فاضي)، نفس الطلب ينرسل تلقائياً لـ Pollinations، والواجهة تكتب لك ملاحظة إن الرد جا من Pollinations.
- لإيقافه: أضف Variable اسمه `FALLBACK_TO_POLLINATIONS` وقيمته `false`.
- مع `openrouter_free`، الانتقال لـ Pollinations يصير بس بعد ما تفشل كل الموديلات في `FREE_MODEL_IDS`.
- لو فشل كل شي، يطلع لك خطأ فيه سبب الفشل من كل موديل.

ملاحظات عن Pollinations:
- ما يحتاج مفتاح API، والكود ما يرسل له هيدر Authorization.
- نفس الـ system prompt ينرسل له بدون أي تغيير.
- يستخدم موديله المجاني (`openai`، وهو حالياً GPT-OSS 20B)، وتقدر تغيّره بمتغير `POLLINATIONS_MODEL`.
- مجاني، بس الاستخدام بدون حساب عليه حدود استخدام عادل من Pollinations نفسها وممكن تتغير. والموديل حقه أكثر تحفّظ من Dolphin في المحتوى الخيالي.
- `APP_PASSWORD` يظل إلزامي مع كل المزودين.

## الموديلات المجانية على OpenRouter (لـ openrouter_free)
**⚠️ تحقق من توفرها قبل التشغيل**: القائمة تتغير باستمرار، والموديل اللي كان مجاني ممكن ينشال أو يصير مدفوع. افتح رابط الموديل وتأكد إنه موجود وسعره 0 قبل ما تحطه في `FREE_MODEL_IDS`. قائمة كل المجاني: https://openrouter.ai/models?max_price=0

**مهم:** حالياً ما فيه ولا موديل مجاني على OpenRouter مصنّف "غير مقيد". كل اللي تحت موديلات عامة بالفلترة العادية، فممكن ترفض بعض الطلبات أكثر من Dolphin. وهذي القائمة كانت متاحة يوم 17 نوفمبر 2026:

| الموديل (لـ `FREE_MODEL_IDS`) | ملاحظة | رابط التحقق |
|---|---|---|
| `google/gemma-4-31b-it:free` | الأول في القائمة الافتراضية، عربيته قوية ومناسب للقصص | https://openrouter.ai/google/gemma-4-31b-it:free |
| `google/gemma-4-26b-a4b-it:free` | أسرع وأخف من اللي فوقه | https://openrouter.ai/google/gemma-4-26b-a4b-it:free |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | موديل كبير، يفكر قبل ما يرد (أبطأ) | https://openrouter.ai/nvidia/nemotron-3-ultra-550b-a55b:free |
| `baidu/ernie-5.5-flash-preview:free` | موديل عام كبير | https://openrouter.ai/baidu/ernie-5.5-flash-preview:free |
| `thinkingmachines/inkling-2-small:free` | موديل عام | https://openrouter.ai/thinkingmachines/inkling-2-small:free |
| `inclusionai/ling-3.2-flash:free` | موديل عام | https://openrouter.ai/inclusionai/ling-3.2-flash:free |
| `dots-studio/dots-3-note-preview:free` | موديل عام | https://openrouter.ai/dots-studio/dots-3-note-preview:free |

موديلات طلبتها وما هي متاحة مجاناً الحين:
- `cognitivecomputations/dolphin-mistral-24b-venice-edition:free`: انشالت النسخة المجانية، والمتاح النسخة المدفوعة بس (استخدمها مع `PROVIDER=openrouter`): https://openrouter.ai/cognitivecomputations/dolphin-mistral-24b-venice-edition
- `nousresearch/hermes-3-llama-3.1-405b:free`: مو موجود. المتاح `nousresearch/hermes-4-405b` وهو مدفوع: https://openrouter.ai/nousresearch/hermes-4-405b
- `stepfun/step-3.5-flash:free`: مو موجود. المتاح من StepFun موديلات مدفوعة مثل `stepfun/step-3.7-flash`: https://openrouter.ai/stepfun/step-3.7-flash

## كيف تضيف موديل جديد بنفسك من OpenRouter
1. روح https://openrouter.ai/models (أو https://openrouter.ai/models?max_price=0 عشان تشوف المجاني بس).
2. اختر أي موديل مجاني (اسمه ينتهي بـ `:free`).
3. انسخ الـ Model ID من صفحة الموديل (مثل `nousresearch/hermes-3-llama-3.1-405b:free`).
4. أضفه في إعدادات الـ Space ← Variables and secrets:
   - إذا `PROVIDER=openrouter_free`: أضفه في `FREE_MODEL_IDS` مفصول بفاصلة عن الباقي، مثال:
     `google/gemma-4-31b-it:free,nousresearch/hermes-3-llama-3.1-405b:free`
   - إذا `PROVIDER=openrouter` (العادي): حطه في `MODEL_ID` (موديل واحد).
5. احفظ، والـ Space يعيد التشغيل لحاله. تأكد من أعلى صفحة الدردشة إن الموديل ظهر.

## تغيير الموديل
- `PROVIDER=openrouter`: عدّل `MODEL_ID` (في `config.py` أو كمتغير في الـ Space).
- `PROVIDER=openrouter_free`: عدّل `FREE_MODEL_IDS` (قائمة مفصولة بفواصل).
- `PROVIDER=pollinations`: عدّل `POLLINATIONS_MODEL` (اختياري).
الواجهة ما تحتاج أي تعديل.

## تعديل الشخصية (system prompt)
- الشخصية موجودة في ملف لحالها اسمه `system_prompt.txt`. افتحه من تبويب Files في الـ Space واضغط Edit، وعدّل النص واحفظ. الـ Space يعيد التشغيل تلقائياً.
- أو بدون ما تلمس الملفات: أضف Variable اسمه `SYSTEM_PROMPT` وحط فيه النص كامل، وهو يتقدم على الملف.
- نفس النص ينرسل لكل المزودين بدون أي تغيير.
- خلّ فيه دايماً سطر اللهجة السعودية وسطر كتابة القصص الطويلة، لأنهم أساس الشخصية.

## تجربة محلية (اختياري)
```
pip install -r requirements.txt
export OPENROUTER_API_KEY=sk-or-...
export APP_PASSWORD=كلمة-سر
uvicorn app:app --port 7860
```
ثم افتح http://localhost:7860


## AI Horde (الإعداد الحالي على Render)
- `PROVIDER=aihorde`: شبكة متطوعين مجانية، بدون بطاقة، تسمح بقصص +18 بين بالغين.
- `AIHORDE_MODEL_IDS`: الموديلات بالترتيب، تفصل بينها فاصلة. القائمة: https://aihorde.net/details/models/text/
- `AIHORDE_API_KEY` (اختياري): مفتاح مجاني من https://aihorde.net/register يخلي دورك أسرع.
- `AIHORDE_PRESENCE_PENALTY` (افتراضي 0.4): يقلل التكرار. هذا الوحيد اللي يقبله AI Horde، وإذا ما فيه جهاز يدعمه ينشال تلقائياً. حطه 0 عشان تطفيه.
- الرد ياخذ تقريباً من نص دقيقة لدقيقتين، والواجهة تعرض "يكتب..." مع عداد ثواني، وتقدر توقف الطلب من الزر الأحمر.

## الواجهة على الآيفون
- مصممة لسفاري: تقدر تضيفها للشاشة الرئيسية (زر المشاركة ← إضافة إلى الشاشة الرئيسية) وتفتح مثل التطبيق.
- المحادثة تنحفظ في المتصفح (localStorage) حتى لو سويت تحديث. زر "جديد" يمسحها، وزر "كمل" يكمل القصة.
