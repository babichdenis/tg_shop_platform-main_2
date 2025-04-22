import os
import django
import logging
from pathlib import Path
from django.contrib.auth import get_user_model
from django.db import connection
from decimal import Decimal


# Настройка логирования
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "data_import.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Укажите корректный путь к настройкам Django-проекта
logging.info("Установка DJANGO_SETTINGS_MODULE...")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.config.settings")
try:
    logging.info("Инициализация Django...")
    django.setup()
    logging.info("Django успешно инициализирован.")
except Exception as e:
    logging.exception(f"Ошибка инициализации Django: {e}")
    raise SystemExit(1)

try:
    logging.info("Импорт моделей...")
    from django_app.shop.models import Category, Product, FAQ
    logging.info("Модели успешно импортированы.")
except Exception as e:
    logging.exception(f"Ошибка при импорте моделей: {e}")
    raise SystemExit(1)

# Получаем модель пользователя
logging.info("Получение модели пользователя...")
User = get_user_model()
logging.info("Модель пользователя получена.")

def create_superuser():
    """Создаёт суперпользователя, если он не существует, используя данные из переменных окружения"""
    try:
        logging.info("Проверка и создание суперпользователя...")
        
        # Получаем данные суперпользователя из переменных окружения
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        
        logging.info(f"Проверка состояния соединения с базой данных...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            logging.info("Соединение с базой данных активно.")
        
        logging.info(f"Проверка существования пользователя '{username}'...")
        user_exists = User.objects.filter(username=username).exists()
        logging.info(f"Пользователь '{username}' существует: {user_exists}")
        
        if not user_exists:
            logging.info(f"Создание суперпользователя '{username}'...")
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            logging.info(f"Суперпользователь успешно создан: {username}/{password}, email: {email}, user id: {user.id}")
        else:
            logging.info("Суперпользователь уже существует.")
        
        logging.info("Функция create_superuser() завершена.")
        
        # Добавим тестовый запрос после проверки
        logging.info("Проверка подключения к базе данных внутри create_superuser()...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            logging.info("Соединение с базой данных всё ещё активно.")
        
        user_count = User.objects.count()
        logging.info(f"Количество пользователей в базе (внутри create_superuser): {user_count}")
    
    except Exception as e:
        logging.exception(f"Ошибка при создании суперпользователя: {e}")
        raise

def get_or_create_category(name: str, parent: Category = None) -> Category:
    """
    Получает существующую категорию по названию или создаёт новую, если не существует.
    """
    try:
        logging.info(f"Попытка создать/получить категорию: {name} (родитель: {parent.name if parent else 'нет родителя'})")
        category, created = Category.objects.get_or_create(
            name=name,
            parent=parent,
            defaults={'is_active': True}
        )
        if created:
            logging.info(f"Создана категория: {name} (родитель: {parent.name if parent else 'нет родителя'})")
        else:
            logging.info(f"Категория уже существует: {name} (родитель: {parent.name if parent else 'нет родителя'})")
        return category
    except Exception as e:
        logging.exception(f"Ошибка при создании категории '{name}': {e}")
        raise

def get_or_create_product(category: Category, name: str, description: str, price: float) -> Product:
    """
    Получает существующий товар по названию и категории или создаёт новый, если не существует.
    """
    try:
        logging.info(f"Попытка создать/получить товар: {name} (категория: {category.name})")
        product, created = Product.objects.get_or_create(
            category=category,
            name=name,
            defaults={
                "description": description,
                "price": Decimal(str(price)),
                "is_active": True
            }
        )
        if created:
            logging.info(f"Создан товар: {name} (категория '{category.name}')")
        else:
            logging.info(f"Товар уже существует: {name}")
        return product
    except Exception as e:
        logging.exception(f"Ошибка при создании товара '{name}': {e}")
        raise

def create_or_update_faq(faq_list):
    """
    Создаёт новые записи FAQ или обновляет существующие по вопросам.
    """
    try:
        logging.info("Начало создания/обновления FAQ...")
        for item in faq_list:
            question = item["question"]
            answer = item["answer"]
            obj, created = FAQ.objects.get_or_create(
                question=question,
                defaults={"answer": answer, "is_active": True}
            )
            if not created:
                obj.answer = answer
                obj.is_active = True
                obj.save()
                logging.info(f"Обновлён существующий FAQ: {question}")
            else:
                logging.info(f"Создан новый FAQ: {question}")
    except Exception as e:
        logging.exception(f"Ошибка при создании/обновлении FAQ: {e}")
        raise

def clear_database():
    """
    Удаляет все данные из таблиц Category, Product и FAQ.
    """
    try:
        logging.info("Начата очистка базы данных...")
        logging.info("Удаление товаров...")
        Product.objects.all().delete()
        logging.info("Товары удалены.")
        logging.info("Удаление категорий...")
        Category.objects.all().delete()
        logging.info("Категории удалены.")
        logging.info("Удаление FAQ...")
        FAQ.objects.all().delete()
        logging.info("FAQ удалены.")
        logging.info("База данных успешно очищена.")
    except Exception as e:
        logging.exception(f"Ошибка при очистке базы данных: {e}")
        raise

def load_categories_and_products(data, parent=None):
    try:
        logging.info("Начало загрузки категорий и товаров...")
        for category_name, subcategories in data.items():
            # Создаем родительскую категорию
            parent_category = get_or_create_category(category_name, parent)
            
            # Обрабатываем подкатегории (если есть)
            if isinstance(subcategories, list):
                for subcat_info in subcategories:
                    # Создаем подкатегорию
                    subcategory = get_or_create_category(subcat_info["name"], parent_category)
                    
                    # Добавляем товары для подкатегории
                    if 'products' in subcat_info:
                        for product_data in subcat_info['products']:
                            get_or_create_product(
                                category=subcategory,
                                name=product_data['name'],
                                description=product_data['description'],
                                price=product_data['price']
                            )
            # Если структура другая (например, товары прямо в категории)
            elif isinstance(subcategories, dict) and 'products' in subcategories:
                for product_data in subcategories['products']:
                    get_or_create_product(
                        category=parent_category,
                        name=product_data['name'],
                        description=product_data['description'],
                        price=product_data['price']
                    )
        logging.info("Загрузка категорий и товаров завершена.")
    except Exception as e:
        logging.exception(f"Ошибка при загрузке категорий и товаров: {e}")
        raise

def main():
    """
    Основная функция для очистки базы данных и добавления новых данных.
    """
    try:
        logging.info("Выполнение скрипта load_data.py...")
        logging.info("Запуск функции create_superuser()...")
        create_superuser()
        logging.info("Функция create_superuser() выполнена успешно.")

        # Тестовый запрос к базе данных
        logging.info("Проверка подключения к базе данных...")
        user_count = User.objects.count()
        logging.info(f"Количество пользователей в базе: {user_count}")

        logging.info("Запуск функции clear_database()...")
        clear_database()
        logging.info("Функция clear_database() выполнена успешно.")

        logging.info("Запуск функции load_categories_and_products()...")
        load_categories_and_products(categories_data)
        logging.info("Функция load_categories_and_products() выполнена успешно.")

        logging.info("Запуск функции create_or_update_faq()...")
        create_or_update_faq(faq_data)
        logging.info("Функция create_or_update_faq() выполнена успешно.")

        logging.info("Данные успешно добавлены в базу данных.")
    except Exception as e:
        logging.exception(f"Ошибка при выполнении load_data.py: {e}")
        raise SystemExit(1)

# Данные для загрузки (структура должна соответствовать ожидаемой)categories_data = {
categories_data = {
    "👕 Одежда": [
        {
            "name": "👔 Мужская одежда",
            "products": [
                {
                    "name": "Футболка мужская, черная",
                    "description": "Классическая черная футболка из хлопка.",
                    "price": 1200.00
                },
                {
                    "name": "Костюм деловой, серый",
                    "description": "Элегантный костюм для деловых встреч.",
                    "price": 15000.00
                },
                {
                    "name": "Джинсы прямого кроя, синие",
                    "description": "Удобные джинсы из плотного денима.",
                    "price": 3000.00
                },
                {
                    "name": "Рубашка классическая, белая",
                    "description": "Классическая белая рубашка из хлопка.",
                    "price": 1800.00
                },
                {
                    "name": "Свитер вязаный, бежевый",
                    "description": "Тёплый вязаный свитер с круглым вырезом.",
                    "price": 2500.00
                },
                {
                    "name": "Шорты повседневные, серые",
                    "description": "Удобные шорты из хлопка для повседневной носки.",
                    "price": 1200.00
                },
                {
                    "name": "Толстовка с капюшоном, синяя",
                    "description": "Толстовка из мягкого флиса с карманом-кенгуру.",
                    "price": 1900.00
                },
                {
                    "name": "Брюки чиносы, хаки",
                    "description": "Универсальные брюки для офиса и прогулок.",
                    "price": 2700.00
                },
                {
                    "name": "Жилет утепленный, черный",
                    "description": "Лёгкий стеганый жилет на молнии.",
                    "price": 2200.00
                },
                {
                    "name": "Куртка кожаная, коричневая",
                    "description": "Куртка из натуральной кожи с подкладкой.",
                    "price": 8000.00
                },
                {
                    "name": "Пиджак повседневный, темно-синий",
                    "description": "Стильный пиджак для повседневных образов.",
                    "price": 5000.00
                },
                {
                    "name": "Джемпер шерстяной, серый",
                    "description": "Уютный джемпер из натуральной шерсти.",
                    "price": 3000.00
                },
                {
                    "name": "Майка базовая, белая",
                    "description": "Базовая майка из хлопка.",
                    "price": 700.00
                },
                {
                    "name": "Спортивные штаны, черные",
                    "description": "Удобные штаны для занятий спортом.",
                    "price": 1500.00
                },
                {
                    "name": "Жакет легкий, бежевый",
                    "description": "Лёгкий жакет для прохладной погоды.",
                    "price": 3500.00
                },
            ],
        },
        {
            "name": "👗 Женская одежда",
            "products": [
                {
                    "name": "Платье летнее, цветочное",
                    "description": "Легкое платье для теплой погоды.",
                    "price": 2500.00
                },
                {
                    "name": "Юбка-карандаш, черная",
                    "description": "Классическая юбка-карандаш для офиса.",
                    "price": 2000.00
                },
                {
                    "name": "Куртка зимняя, красная",
                    "description": "Теплая куртка с капюшоном.",
                    "price": 7500.00
                },
                {
                    "name": "Блузка шелковая, голубая",
                    "description": "Легкая шелковая блузка с коротким рукавом.",
                    "price": 1900.00
                },
                {
                    "name": "Кардиган уютный, бежевый",
                    "description": "Уютный кардиган крупной вязки.",
                    "price": 2200.00
                },
                {
                    "name": "Шорты джинсовые, голубые",
                    "description": "Короткие джинсовые шорты с потертостями.",
                    "price": 1300.00
                },
                {
                    "name": "Костюм брючный, черный",
                    "description": "Классический женский брючный костюм.",
                    "price": 8000.00
                },
                {
                    "name": "Футболка свободного кроя, белая",
                    "description": "Универсальная женская футболка.",
                    "price": 900.00
                },
                {
                    "name": "Платье коктейльное, красное",
                    "description": "Стильное платье для особых случаев.",
                    "price": 4000.00
                },
                {
                    "name": "Жилет стеганый, розовый",
                    "description": "Легкий стеганый жилет на пуговицах.",
                    "price": 1500.00
                },
                {
                    "name": "Свитер оверсайз, серый",
                    "description": "Комфортный свитер свободного силуэта.",
                    "price": 2000.00
                },
                {
                    "name": "Пальто демисезонное, бежевое",
                    "description": "Стильное пальто на пуговицах.",
                    "price": 5000.00
                },
                {
                    "name": "Брюки классические, темно-синие",
                    "description": "Классические брюки для деловых образов.",
                    "price": 2800.00
                },
                {
                    "name": "Сарафан летний, желтый",
                    "description": "Легкий сарафан на бретелях.",
                    "price": 1500.00
                },
                {
                    "name": "Куртка джинсовая, синяя",
                    "description": "Классическая джинсовая куртка.",
                    "price": 2700.00
                },
            ],
        },
        {
            "name": "🧣 Аксессуары",
            "products": [
                {
                    "name": "Часы наручные, кожаный ремешок",
                    "description": "Стильные часы с аналоговым механизмом.",
                    "price": 4500.00
                },
                {
                    "name": "Солнцезащитные очки, унисекс",
                    "description": "Очки с защитой от ультрафиолета.",
                    "price": 1500.00
                },
                {
                    "name": "Ремень кожаный, черный",
                    "description": "Классический ремень для брюк.",
                    "price": 1800.00
                },
                {
                    "name": "Кошелек женский, красный",
                    "description": "Компактный кошелек из искусственной кожи.",
                    "price": 1200.00
                },
                {
                    "name": "Шляпа летняя, соломенная",
                    "description": "Лёгкая шляпа для защиты от солнца.",
                    "price": 800.00
                },
                {
                    "name": "Перчатки кожаные, черные",
                    "description": "Кожаные перчатки с подкладкой.",
                    "price": 1300.00
                },
                {
                    "name": "Шарф теплый, серый",
                    "description": "Шерстяной шарф для холодной погоды.",
                    "price": 900.00
                },
                {
                    "name": "Очки для чтения, +1.5 диоптрий",
                    "description": "Удобные очки с диоптрией +1.5.",
                    "price": 700.00
                },
                {
                    "name": "Зонт складной, синий",
                    "description": "Компактный зонт с автоматическим механизмом.",
                    "price": 1000.00
                },
                {
                    "name": "Носки спортивные (набор 3 шт.)",
                    "description": "Удобные носки для тренировок.",
                    "price": 500.00
                },
                {
                    "name": "Сумка через плечо, коричневая",
                    "description": "Сумка среднего размера с регулируемым ремнем.",
                    "price": 2000.00
                },
                {
                    "name": "Браслет серебряный",
                    "description": "Изящный серебряный браслет.",
                    "price": 2500.00
                },
                {
                    "name": "Кольцо с камнем",
                    "description": "Стильное кольцо с декоративным камнем.",
                    "price": 3000.00
                },
                {
                    "name": "Подтяжки классические, черные",
                    "description": "Подтяжки для брюк с регулируемой длиной.",
                    "price": 700.00
                },
                {
                    "name": "Ремешок для часов, силиконовый",
                    "description": "Универсальный ремешок для спортивных часов.",
                    "price": 600.00
                },
            ],
        },
    ],
    "⚽ Спорт": [
        {
            "name": "🏋️‍♂️ Тренажёры",
            "products": [
                {
                    "name": "Беговая дорожка",
                    "description": "Электрическая беговая дорожка для дома.",
                    "price": 35000.00
                },
                {
                    "name": "Гантели 10 кг",
                    "description": "Удобные гантели с покрытием.",
                    "price": 2000.00
                },
                {
                    "name": "Эллиптический тренажёр",
                    "description": "Компактный тренажёр для кардиотренировок.",
                    "price": 25000.00
                },
                {
                    "name": "Гимнастический мяч",
                    "description": "Мяч для фитнеса и гимнастики.",
                    "price": 800.00
                },
                {
                    "name": "Турник настенный",
                    "description": "Надежный настенный турник для дома.",
                    "price": 1500.00
                },
                {
                    "name": "Велотренажёр магнитный",
                    "description": "Тихий велотренажёр с плавным ходом.",
                    "price": 18000.00
                },
                {
                    "name": "Скамья для жима",
                    "description": "Регулируемая скамья для жима лёжа.",
                    "price": 5000.00
                },
                {
                    "name": "Комплект эспандеров",
                    "description": "Набор резиновых эспандеров разного сопротивления.",
                    "price": 900.00
                },
                {
                    "name": "Набор гантелей 1-5 кг",
                    "description": "Набор для базовых упражнений.",
                    "price": 3500.00
                },
                {
                    "name": "Тренажёр для пресса",
                    "description": "Складной тренажёр для эффективных упражнений.",
                    "price": 2500.00
                },
                {
                    "name": "Перекладина для подтягиваний",
                    "description": "Многофункциональный турник для дверного проёма.",
                    "price": 1200.00
                },
                {
                    "name": "Гиперэкстензия",
                    "description": "Тренажёр для развития мышц спины и поясницы.",
                    "price": 4500.00
                },
                {
                    "name": "Степпер компактный",
                    "description": "Компактный степпер для кардионагрузок.",
                    "price": 3000.00
                },
                {
                    "name": "Гребной тренажёр",
                    "description": "Многофункциональный тренажёр для кардио и мышц.",
                    "price": 20000.00
                },
                {
                    "name": "Платформа для стэп-аэробики",
                    "description": "Устойчивая платформа для фитнеса и аэробики.",
                    "price": 2500.00
                },
            ],
        },
        {
            "name": "👟 Спортивная обувь",
            "products": [
                {
                    "name": "Кроссовки беговые",
                    "description": "Лёгкие и удобные кроссовки для бега.",
                    "price": 5000.00
                },
                {
                    "name": "Бутсы для футбола",
                    "description": "Качественная обувь для игр на траве.",
                    "price": 4500.00
                },
                {
                    "name": "Кеды повседневные",
                    "description": "Удобные кеды для повседневной носки.",
                    "price": 2000.00
                },
                {
                    "name": "Кроссовки баскетбольные",
                    "description": "Высокие кроссовки с усиленной поддержкой.",
                    "price": 6000.00
                },
                {
                    "name": "Кроссовки для тенниса",
                    "description": "Обувь с устойчивой подошвой.",
                    "price": 5500.00
                },
                {
                    "name": "Кроссовки легкие для ходьбы",
                    "description": "Мягкая амортизация для долгих прогулок.",
                    "price": 3500.00
                },
                {
                    "name": "Кроссовки для тренировок в зале",
                    "description": "Универсальная модель с поддержкой стопы.",
                    "price": 4000.00
                },
                {
                    "name": "Кроссовки с амортизацией",
                    "description": "Дополнительная поддержка пятки и свода.",
                    "price": 4500.00
                },
                {
                    "name": "Бутсы с металлическими шипами",
                    "description": "Для профессиональной игры на траве.",
                    "price": 7000.00
                },
                {
                    "name": "Футзалки",
                    "description": "Обувь для игры в зале с нескользящей подошвой.",
                    "price": 3000.00
                },
                {
                    "name": "Сланцы для душа",
                    "description": "Лёгкие сланцы с рельефной стелькой.",
                    "price": 800.00
                },
                {
                    "name": "Кроссовки для хайкинга",
                    "description": "Прочная обувь для пересечённой местности.",
                    "price": 5500.00
                },
                {
                    "name": "Кеды с высокой шнуровкой",
                    "description": "Стильные кеды для городских прогулок.",
                    "price": 2500.00
                },
                {
                    "name": "Сандалии спортивные",
                    "description": "Удобные сандалии для активного отдыха.",
                    "price": 2200.00
                },
                {
                    "name": "Кроссовки для скейтборда",
                    "description": "Усиленная подошва и защита носка.",
                    "price": 3800.00
                },
            ],
        },
    ],
}
faq_data = [
    {
        "question": "Что такое бот-магазин и как он работает?",
        "answer": "Это Telegram-бот, позволяющий просматривать каталог товаров, добавлять их в корзину и совершать покупку прямо в чате."
    },
    {
        "question": "Как сделать заказ?",
        "answer": "Просто напишите нам в личные сообщения, выберите товар из каталога или уточните детали, и мы оформим заказ."
    },
    {
        "question": "Где посмотреть каталог товаров?",
        "answer": "Нажмите кнопку «Каталог» в меню бота или запросите актуальный список товаров у нашего менеджера."
    },
    {
        "question": "Как узнать наличие товара?",
        "answer": "Напишите нам название или артикул товара, и мы оперативно проверим его наличие."
    },
    {
        "question": "Есть ли у вас доставка?",
        "answer": "Да, мы доставляем заказы по [указать регионы/страны]. Подробнее о сроках и условиях можно узнать в разделе «Доставка»."
    },
    {
        "question": "Как отследить мой заказ?",
        "answer": "После отправки мы пришлем вам трек-номер или данные для отслеживания. Также вы всегда можете уточнить статус заказа у нас в чате."
    },
    {
        "question": "Можно ли изменить или отменить заказ?",
        "answer": "Да, если заказ еще не собран или не отправлен. Свяжитесь с нами как можно скорее, и мы внесем изменения."
    },
    {
        "question": "Как связаться с поддержкой?",
        "answer": "Напишите нам в этот чат, и мы ответим в ближайшее время. Также вы можете позвонить нам по номеру [номер телефона]."
    },
    {
        "question": "Есть ли у вас гарантия на товары?",
        "answer": "Да, на все товары предоставляется гарантия [срок гарантии]. Подробности уточняйте при покупке."
    },
    {
        "question": "Можно ли вернуть товар?",
        "answer": "Да, в течение [срок возврата] дней при соблюдении условий возврата. Товар должен быть в оригинальной упаковке и без следов использования."
    },
    {
        "question": "Как часто обновляется ассортимент?",
        "answer": "Мы регулярно добавляем новинки. Чтобы быть в курсе, подпишитесь на наши новости или проверяйте каталог."
    },
    {
        "question": "Есть ли у вас скидки для постоянных клиентов?",
        "answer": "Да! Мы ценим наших покупателей и предлагаем бонусы, акции и персональные скидки. Следите за новостями!"
    },
    {
        "question": "Можно ли заказать товар, которого нет в каталоге?",
        "answer": "Да, напишите нам название или фото товара, и мы постараемся найти его для вас."
    },
    {
        "question": "Как оставить отзыв о покупке?",
        "answer": "Мы будем рады вашему отзыву! Напишите нам свои впечатления, и мы разместим его в нашем канале/группе."
    },
    {
        "question": "Работаете ли вы с оптовыми заказами?",
        "answer": "Да, предоставляем специальные условия для оптовых покупателей. Напишите нам для уточнения деталей."
    }
]
if __name__ == "__main__":
    main()
