## Логика работы бота EnglishCard

При запуске данного бота Телеграма EnglishCard приветствует пользователя и предлагает начать тренировку по команде /cards.

При выполнении команды /cards бот формирует случайную карточку слов из общего и индвидуального словарей пользователя, которые предварительно загружены в БД из приложенного JSON-файла. Далее пользователю предлагается выбрать русскому слову соответствующее английское слово из четырех предложенных.

При правильном или неправильном ответе слово помечается галочкой или крестиком соответственно.

При нажатии на кнопку "Дальше ⏭" будет сформирована следующая карточка слов.

При нажатии на кнопку "Добавить слово ➕" будет предложено ввести новое английское слово. После ввода данное слово будет проверено на корректность введенных символов и отсутствие его в БД. В случае, если проверка не пройдет, бот отправит соответствующее сообщение. После успешного прохождения проверки будет предложено ввести русское слово для перевода введенного английского слова. Далее данное русское слово будет также проверено на корректность введенных символов и отсутствие его в БД. В случае, если проверка не пройдет, бот отправит соответствующее сообщение. В случае успеха бот отправит сообщение, что пара введенных слов успешно добавлены в словарь пользователя, а также выведет сообщение сколько слов уже находится в индивидуальном словаре пользователя.

При нажатии на кнопку "Удалить слово🔙" бот предложит ввести английское слово для удаления. После ввода данное слово будет проверено на корректность введенных символов и присутствие его в БД. В случае, если проверка не пройдет, бот отправит соответствующее сообщение. В случае успеха бот отправит сообщение, что запись из БД успешно удалена.