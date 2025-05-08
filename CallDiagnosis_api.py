import requests
from flask import Flask, render_template, request, url_for, redirect
from datetime import datetime
from database import DatabaseManager

"""
Класс для запуска веб-приложения Flask, которое вызывает внешний Java-сервис для постановки диагноза на основе Drools правил.
"""

class DiagnosisWebApp:

    def __init__(self, api_url, template_name='index.html'):

        self.api_url = api_url              # URL запущенного Java сервиса
        self.template_name = template_name  # Имя HTML файла
        self.app = Flask(__name__)          # Создаем экземпляр Flask приложения
        
        # Инициализируем менеджер БД
        self.db_manager = DatabaseManager() # Использует DB_NAME из database.py

        self._setup_routes() # Настраиваем маршруты после создания self.app

    def _call_diagnosis_api(self, chest_pain, ecg_abnormal, troponin_high, heart_rate, systolic_bp):
        """
        Вызывает внешний API для получения диагноза.
        """
        params = {
            'chestPain': str(chest_pain).lower(),
            'ecgAbnormal': str(ecg_abnormal).lower(),
            'troponinHigh': str(troponin_high).lower(),
            'heartRate': str(heart_rate) if heart_rate is not None else '',
            'systolicBP': str(systolic_bp) if systolic_bp is not None else ''
        }

        try:
            response = requests.get(self.api_url
                                    , params=params
                                    , timeout=10 # Устанавливаем небольшой таймаут, чтобы избежать зависания
                                    )
            
            response.raise_for_status() # Вызовет исключение для кодов ошибок HTTP (4xx, 5xx)

            return response.text # Возвращаем текст диагноза

        except requests.exceptions.ConnectionError:
            return f"Ошибка подключения: Не удалось подключиться к API ({self.api_url}). Убедитесь, что Java-сервис с правилами запущен."
        except requests.exceptions.Timeout:
            return f"Ошибка таймаута: Превышено время ожидания ответа от API ({self.api_url})."
        except requests.exceptions.RequestException as e:
            # Попытаемся получить текст ошибки от сервера, если он есть
            error_detail = e.response.text if e.response is not None else str(e)
            status_code = e.response.status_code if e.response is not None else 'N/A'
            return f"Ошибка API ({status_code}): {error_detail}"
        except Exception as e:
            return f"Неожиданная ошибка Python при вызове API: {e}"

    def _setup_routes(self):
        """
        Настраивает маршруты Flask для приложения. Используется add_url_rule, так как декораторы @self.app.route не могут быть применены напрямую к методам до инициализации self.app.
        """
        self.app.add_url_rule('/', view_func=self.index, methods=['GET', 'POST'])

        # Добавим маршрут для очистки формы (переход к новому пациенту)
        self.app.add_url_rule('/new', view_func=self.new_patient, methods=['GET'])
    
    def new_patient(self):
        """Перенаправляет на главную страницу без ID пациента."""
        return redirect(url_for('index'))

    def index(self):
        """
        Обработчик маршрута для главной страницы ('/'). Обрабатывает GET (отображение формы) и POST (обработка отправки формы).
        """
        diagnosis_result = None # Изначально результата нет

        save_message = None
        form_error = None
        selected_patient_id = None # ID пациента, чьи данные загружены

        selected_visit_id = None
        patients_list = []
        visits_list = [] # Список визитов для выбранного пациента
        
        # Форматтер для datetime-local input
        dt_local_format = '%Y-%m-%dT%H:%M'
        db_datetime_format = '%Y-%m-%d %H:%M:%S'

        # Данные для формы по умолчанию
        input_data = {
            'patient_id': None, 'patient_name': '', 'visit_id': None,
            # Устанавливаем текущую дату/время по умолчанию, форматированную для input
            'visit_date': datetime.now().strftime(dt_local_format),
            'chestPain': False, 'ecgAbnormal': False, 'troponinHigh': False,
            'heartRate': 0, 'systolicBP': 0
        }

        patients_list = self.db_manager.get_all_patients_list()

        # --- Обработка GET запроса ---
        if request.method == 'GET':
            try:
                req_patient_id = request.args.get('patient_id', type=int)
                req_visit_id = request.args.get('visit_id', type=int)

                if req_patient_id:
                    selected_patient_id = req_patient_id
                    visits_list = self.db_manager.get_patient_visits(selected_patient_id)

                    patient_info = next((p for p in patients_list if p['id'] == selected_patient_id), None)
                    if patient_info:
                        input_data['patient_name'] = patient_info['name'] # Устанавливаем имя, даже если визит не выбран
                        input_data['patient_id'] = selected_patient_id

                    if req_visit_id:
                        selected_visit_id = req_visit_id
                        visit_data = self.db_manager.get_visit_data_by_id(selected_visit_id)
                        if visit_data and visit_data['patient_id'] == selected_patient_id:
                            # Заполняем input_data данными визита
                            input_data['patient_id'] = visit_data['patient_id']
                            input_data['patient_name'] = visit_data['patient_name'] # Перезаписываем на всякий случай
                            input_data['visit_id'] = visit_data['visit_id']
                            # --- Ключевое: Форматирование даты из БД для input ---
                            try:
                                db_date_str = visit_data['visit_date']
                                dt_obj = datetime.strptime(db_date_str, db_datetime_format)
                                input_data['visit_date'] = dt_obj.strftime(dt_local_format) # Формат для HTML
                            except (ValueError, TypeError):
                                print(f"Ошибка форматирования даты из БД: {visit_data.get('visit_date')}")
                                input_data['visit_date'] = '' # Поле будет пустым при ошибке
                            # --- Остальные поля ---
                            input_data['chestPain'] = bool(visit_data['chest_pain'])
                            input_data['ecgAbnormal'] = bool(visit_data['ecg_abnormal'])
                            input_data['troponinHigh'] = bool(visit_data['troponin_high'])
                            input_data['heartRate'] = visit_data['heart_rate'] if visit_data['heart_rate'] is not None else 0
                            input_data['systolicBP'] = visit_data['systolic_bp'] if visit_data['systolic_bp'] is not None else 0
                        else:
                            # Визит не найден или не принадлежит пациенту, сбрасываем ID визита
                            selected_visit_id = None
                            # Дата сбрасывается на текущую (установлена по умолчанию)
                            input_data['visit_date'] = datetime.now().strftime(dt_local_format)
                    else:
                         # Только пациент выбран, дата сбрасывается на текущую
                         input_data['visit_date'] = datetime.now().strftime(dt_local_format)

            except ValueError:
                print("Ошибка: Некорректный ID пациента или визита в URL.")

        # --- Обработка POST запроса ---
        elif request.method == 'POST':
            action = request.form.get('action')
            patient_name_from_form = request.form.get('patient_name', '').strip()
            # --- Получаем дату из поля datetime-local ---
            visit_date_str_from_form = request.form.get('visit_date')
            # --- Получаем остальные данные из скрытых полей ---
            chest_pain_str = request.form.get('chestPain', '')
            ecg_abnormal_str = request.form.get('ecgAbnormal', '')
            troponin_high_str = request.form.get('troponinHigh', '')
            heart_rate_str = request.form.get('heartRate')
            systolic_bp_str = request.form.get('systolicBP')
            current_patient_id_str = request.form.get('current_patient_id') # ID пациента, который БЫЛ на форме
            # current_visit_id_str = request.form.get('current_visit_id') # Не нужен для логики сохранения

            # --- Парсинг и заполнение input_data для перерисовки ---
            chest_pain = chest_pain_str.lower() == 'true' if chest_pain_str else False
            ecg_abnormal = ecg_abnormal_str.lower() == 'true' if ecg_abnormal_str else False
            troponin_high = troponin_high_str.lower() == 'true' if troponin_high_str else False
            input_data['patient_name'] = patient_name_from_form
            input_data['visit_date'] = visit_date_str_from_form if visit_date_str_from_form else datetime.now().strftime(dt_local_format) # Сохраняем введенное для формы
            input_data['chestPain'] = chest_pain
            input_data['ecgAbnormal'] = ecg_abnormal
            input_data['troponinHigh'] = troponin_high
            if current_patient_id_str: # Запоминаем, кто был выбран, для подсветки
                 try: selected_patient_id = int(current_patient_id_str); input_data['patient_id'] = selected_patient_id
                 except ValueError: selected_patient_id = None

            # Парсинг чисел
            heart_rate = None
            systolic_bp = None
            try:
                if heart_rate_str: heart_rate = float(heart_rate_str)
                input_data['heartRate'] = heart_rate if heart_rate is not None else 0
                if systolic_bp_str: systolic_bp = float(systolic_bp_str)
                input_data['systolicBP'] = systolic_bp if systolic_bp is not None else 0
            except ValueError:
                form_error = "Ошибка ввода: ЧСС и АД должны быть числами."
                if 'heartRate' in request.form: input_data['heartRate'] = request.form['heartRate']
                if 'systolicBP' in request.form: input_data['systolicBP'] = request.form['systolicBP']


            # --- Логика действия ---
            if action == 'save':
                # 1. Валидация даты из формы
                visit_date_to_save = None # Дата в формате БД
                if not visit_date_str_from_form:
                    form_error = "Ошибка: Дата визита не указана."
                else:
                    try:
                        # Парсим дату из формата input datetime-local
                        dt_obj = datetime.strptime(visit_date_str_from_form, dt_local_format)
                        # Форматируем для сохранения в БД
                        visit_date_to_save = dt_obj.strftime(db_datetime_format)
                    except ValueError:
                        form_error = "Ошибка: Некорректный формат даты визита."

                # 2. Валидация имени
                if not form_error and not patient_name_from_form:
                    form_error = "Ошибка: Необходимо указать имя пациента."

                # 3. Основная логика сохранения (упрощенная)
                if not form_error:
                    # Получаем ID пациента по имени из формы (создаем, если нет)
                    patient_id = self.db_manager.get_or_create_patient_id(patient_name_from_form)

                    if patient_id:
                        # Сохраняем новый визит с введенными данными и ДАТОЙ ИЗ ФОРМЫ
                        new_visit_id = self.db_manager.save_visit_data(
                            patient_id, visit_date_to_save, chest_pain, ecg_abnormal,
                            troponin_high, heart_rate, systolic_bp
                        )
                        if new_visit_id:
                            save_message = f"Визит для '{patient_name_from_form}' от {visit_date_to_save} сохранен (ID визита: {new_visit_id})."
                            # Обновляем списки для отображения
                            patients_list = self.db_manager.get_all_patients_list()
                            visits_list = self.db_manager.get_patient_visits(patient_id)
                            # Устанавливаем выбранные ID для подсветки
                            selected_patient_id = patient_id
                            selected_visit_id = new_visit_id
                            # Обновляем данные в input_data для корректной перерисовки формы
                            input_data['patient_id'] = patient_id
                            input_data['visit_id'] = new_visit_id
                            # input_data['visit_date'] уже содержит дату из формы
                        else:
                            form_error = "Ошибка при сохранении данных визита в базу."
                    else:
                         form_error = "Ошибка при поиске или создании пациента в базе."

            elif action == 'diagnose':
                 # Проверяем числовые поля перед вызовом API
                 if not form_error:
                     print(f"Отправка в API: chestPain={chest_pain}, ecgAbnormal={ecg_abnormal}, troponinHigh={troponin_high}, heartRate={heart_rate}, systolicBP={systolic_bp}")
                     diagnosis_result = self._call_diagnosis_api(
                         chest_pain, ecg_abnormal, troponin_high, heart_rate, systolic_bp
                     )
                     print(f"Результат от API: {diagnosis_result}")
                     # После диагностики нужно перезагрузить список визитов, если пациент был выбран
                     if selected_patient_id:
                          visits_list = self.db_manager.get_patient_visits(selected_patient_id)


            # Если была ошибка формы (валидация даты или чисел), diagnosis_result будет None

            # Перезагружаем список визитов в конце POST, если пациент выбран
            if selected_patient_id and not visits_list:
                 visits_list = self.db_manager.get_patient_visits(selected_patient_id)


        # Отображаем шаблон
        return render_template(
            self.template_name,
            diagnosis=diagnosis_result,
            inputs=input_data, # Содержит дату, отформатированную для input
            patients=patients_list,
            visits=visits_list,
            selected_patient_id=selected_patient_id,
            selected_visit_id=selected_visit_id,
            save_message=save_message,
            form_error=form_error
        )

    def run(self, host='127.0.0.1', port=5000, debug=True):
        print(f"Запуск Flask приложения на http://{host}:{port}/")
        self.app.run(host=host, port=port, debug=debug, use_reloader=False if debug else True)

if __name__ == '__main__':
    DIAGNOSIS_API_URL = "http://localhost:8080/run-rules"
    web_app = DiagnosisWebApp(api_url=DIAGNOSIS_API_URL, template_name='index.html')
    web_app.run(debug=True)