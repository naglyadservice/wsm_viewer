// JavaScript для страницы device.html
document.addEventListener('DOMContentLoaded', function() {
    const deviceId = document.getElementById('device-container').dataset.deviceId;
    
    // Функция для получения состояния устройства
    function getDeviceState() {
        fetch(`/api/devices/${deviceId}/state/info`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Не удалось получить состояние устройства');
                }
                return response.json();
            })
            .then(data => {
                updateDeviceStateUI(data);
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showError('Ошибка получения данных состояния: ' + error.message);
            });
    }
    
    // Функция для обновления UI с данными состояния
    function updateDeviceStateUI(data) {
        // Обновление основных показателей
        document.getElementById('operating-mode').textContent = translateOperatingMode(data.operatingMode);
        document.getElementById('summa-in-box').textContent = formatMoney(data.summaInBox);
        document.getElementById('liters-in-tank').textContent = formatLiters(data.litersInTank);
        
        // Обновление статусов сенсоров
        document.getElementById('tank-low-level').innerHTML = getBadgeHtml(data.tankLowLevelSensor);
        document.getElementById('tank-high-level').innerHTML = getBadgeHtml(data.tankHighLevelSensor);
        document.getElementById('deposit-box').innerHTML = getBadgeHtml(data.depositBoxSensor);
        document.getElementById('door-sensor').innerHTML = getBadgeHtml(data.doorSensor);
        
        // Обновление состояния валидаторов
        document.getElementById('coin-state').textContent = data.coinState;
        document.getElementById('bill-state').textContent = data.billState;
        
        // Обновление ошибок
        const errorsContainer = document.getElementById('errors-container');
        errorsContainer.innerHTML = '';
        
        if (data.errors) {
            let hasErrors = false;
            Object.entries(data.errors).forEach(([key, value]) => {
                if (value === true) {
                    hasErrors = true;
                    const errorBadge = document.createElement('div');
                    errorBadge.className = 'badge badge-danger mr-2 mb-2';
                    errorBadge.textContent = key;
                    errorsContainer.appendChild(errorBadge);
                }
            });
            
            if (!hasErrors) {
                errorsContainer.innerHTML = '<p class="text-success">Ошибок не обнаружено</p>';
            }
        } else {
            errorsContainer.innerHTML = '<p class="text-success">Ошибок не обнаружено</p>';
        }
        
        // Обновляем время последнего обновления
        document.getElementById('last-update').textContent = formatDateTime(data.created);
        
        // Скрываем сообщение об ошибке, если оно было
        hideError();
    }
    
    // Функция для запроса настроек устройства
    function requestDeviceSettings() {
        // Очистка предыдущего состояния форм и сообщений
        document.getElementById('settings-form').classList.add('d-none');
        document.getElementById('btn-save-settings').classList.add('d-none');
        document.getElementById('settings-loading').classList.remove('d-none');
        hideError();
        
        showMessage('Запрос настроек отправлен...');
        
        fetch(`/api/devices/${deviceId}/settings/request`)
            .then(response => response.json())
            .then(data => {
                showMessage('Запрос настроек отправлен. Ожидание ответа (5 сек)...');
                
                // Ждем 5 секунд и пытаемся получить настройки один раз
                setTimeout(() => {
                    getDeviceSettings();
                }, 5000);
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Ошибка при запросе настроек: ' + error.message);
            });
    }
    
    // Функция для получения настроек устройства
    function getDeviceSettings() {
        fetch(`/api/devices/${deviceId}/settings`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('Устройство не ответило. Попробуйте запросить настройки снова.');
                    }
                    throw new Error('Ошибка получения настроек');
                }
                return response.json();
            })
            .then(data => {
                fillSettingsForm(data);
                showMessage('Настройки успешно получены');
            })
            .catch(error => {
                console.error('Error:', error);
                showError(error.message);
                // Возвращаем форму к состоянию ожидания запроса
                document.getElementById('settings-loading').classList.remove('d-none');
            });
    }
    
    // Функция для заполнения формы настроек
    function fillSettingsForm(data) {
        document.getElementById('settings-loading').classList.add('d-none');
        document.getElementById('settings-form').classList.remove('d-none');
        document.getElementById('btn-save-settings').classList.remove('d-none');
        
        // Заполняем поля формы данными
        document.getElementById('maxPayment').value = data.maxPayment || '';
        document.getElementById('minPayPass').value = data.minPayPass || '';
        document.getElementById('maxPayPass').value = data.maxPayPass || '';
        document.getElementById('deltaPayPass').value = data.deltaPayPass || '';
        document.getElementById('tariffPerLiter_1').value = data.tariffPerLiter_1 || '';
        document.getElementById('tariffPerLiter_2').value = data.tariffPerLiter_2 || '';
        document.getElementById('pulsesPerLiter_1').value = data.pulsesPerLiter_1 || '';
        document.getElementById('pulsesPerLiter_2').value = data.pulsesPerLiter_2 || '';
        document.getElementById('pulsesPerLiter_3').value = data.pulsesPerLiter_3 || '';
        document.getElementById('timeOnePay').value = data.timeOnePay || '';
        document.getElementById('litersInFullTank').value = data.litersInFullTank || '';
        document.getElementById('timeServisMode').value = data.timeServisMode || '';
        document.getElementById('spillTimer').value = data.spillTimer || '';
        document.getElementById('spillAmount').value = data.spillAmount || '';
    }
    
    // Функция для сохранения настроек
    function saveSettings() {
        const formData = {
            maxPayment: parseInt(document.getElementById('maxPayment').value) || 0,
            minPayPass: parseInt(document.getElementById('minPayPass').value) || 0,
            maxPayPass: parseInt(document.getElementById('maxPayPass').value) || 0,
            deltaPayPass: parseInt(document.getElementById('deltaPayPass').value) || 0,
            tariffPerLiter_1: parseInt(document.getElementById('tariffPerLiter_1').value) || 0,
            tariffPerLiter_2: parseInt(document.getElementById('tariffPerLiter_2').value) || 0,
            pulsesPerLiter_1: parseInt(document.getElementById('pulsesPerLiter_1').value) || 0,
            pulsesPerLiter_2: parseInt(document.getElementById('pulsesPerLiter_2').value) || 0,
            pulsesPerLiter_3: parseInt(document.getElementById('pulsesPerLiter_3').value) || 0,
            timeOnePay: parseInt(document.getElementById('timeOnePay').value) || 0,
            litersInFullTank: parseInt(document.getElementById('litersInFullTank').value) || 0,
            timeServisMode: parseInt(document.getElementById('timeServisMode').value) || 0,
            spillTimer: parseInt(document.getElementById('spillTimer').value) || 0,
            spillAmount: parseInt(document.getElementById('spillAmount').value) || 0
        };
        
        fetch(`/api/devices/${deviceId}/settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сохранения настроек');
            }
            return response.json();
        })
        .then(data => {
            showMessage('Настройки отправлены в устройство, ожидание подтверждения...');
            // Начинаем проверять ACK
            setTimeout(checkSettingsAck, 1000);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ошибка при сохранении настроек: ' + error.message);
        });
    }
    
    // Функция для запроса конфигурации устройства
    function requestDeviceConfig() {
        // Очистка предыдущего состояния форм и сообщений
        document.getElementById('config-form').classList.add('d-none');
        document.getElementById('btn-save-config').classList.add('d-none');
        document.getElementById('config-loading').classList.remove('d-none');
        hideError();
        
        showMessage('Запрос конфигурации отправлен...');
        
        fetch(`/api/devices/${deviceId}/config/request`)
            .then(response => response.json())
            .then(data => {
                showMessage('Запрос конфигурации отправлен. Ожидание ответа (5 сек)...');
                
                // Ждем 5 секунд и пытаемся получить конфигурацию один раз
                setTimeout(() => {
                    getDeviceConfig();
                }, 5000);
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Ошибка при запросе конфигурации: ' + error.message);
            });
    }
    
    // Функция для получения конфигурации устройства
    function getDeviceConfig() {
        fetch(`/api/devices/${deviceId}/config`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('Устройство не ответило. Попробуйте запросить конфигурацию снова.');
                    }
                    throw new Error('Ошибка получения конфигурации');
                }
                return response.json();
            })
            .then(data => {
                fillConfigForm(data);
                showMessage('Конфигурация успешно получена');
            })
            .catch(error => {
                console.error('Error:', error);
                showError(error.message);
                // Возвращаем форму к состоянию ожидания запроса
                document.getElementById('config-loading').classList.remove('d-none');
            });
    }
    
    // Функция для заполнения формы конфигурации
    function fillConfigForm(data) {
        document.getElementById('config-loading').classList.add('d-none');
        document.getElementById('config-form').classList.remove('d-none');
        document.getElementById('btn-save-config').classList.remove('d-none');
        
        // Заполняем поля формы данными
        document.getElementById('wifi_STA_ssid').value = data.wifi_STA_ssid || '';
        document.getElementById('wifi_STA_pass').value = data.wifi_STA_pass || '';
        document.getElementById('ntp_server').value = data.ntp_server || '';
        document.getElementById('timeZone').value = data.timeZone || '';
        document.getElementById('broker_uri').value = data.broker_uri || '';
        document.getElementById('broker_port').value = data.broker_port || '';
        document.getElementById('broker_user').value = data.broker_user || '';
        document.getElementById('broker_pass').value = data.broker_pass || '';
        document.getElementById('OTA_server').value = data.OTA_server || '';
        document.getElementById('OTA_port').value = data.OTA_port || '';
        
        // Обрабатываем массивы
        if (data.bill_table && Array.isArray(data.bill_table)) {
            document.getElementById('bill_table').value = data.bill_table.join(',');
        }
        
        if (data.coin_table && Array.isArray(data.coin_table)) {
            document.getElementById('coin_table').value = data.coin_table.join(',');
        }
        
        // Выбираем правильное значение в выпадающем списке
        if (data.coinValidatorType) {
            document.getElementById('coinValidatorType').value = data.coinValidatorType;
        }
        
        document.getElementById('coinPulsePrice').value = data.coinPulsePrice || '';
    }
    
    // Функция для сохранения конфигурации
    function saveConfig() {
        const formData = {
            wifi_STA_ssid: document.getElementById('wifi_STA_ssid').value,
            wifi_STA_pass: document.getElementById('wifi_STA_pass').value,
            ntp_server: document.getElementById('ntp_server').value,
            timeZone: parseInt(document.getElementById('timeZone').value) || 0,
            broker_uri: document.getElementById('broker_uri').value,
            broker_port: parseInt(document.getElementById('broker_port').value) || 0,
            broker_user: document.getElementById('broker_user').value,
            broker_pass: document.getElementById('broker_pass').value,
            OTA_server: document.getElementById('OTA_server').value,
            OTA_port: parseInt(document.getElementById('OTA_port').value) || 0,
            coinValidatorType: document.getElementById('coinValidatorType').value,
            coinPulsePrice: parseInt(document.getElementById('coinPulsePrice').value) || 0
        };
        
        // Обрабатываем массивы
        const billTableStr = document.getElementById('bill_table').value;
        if (billTableStr) {
            formData.bill_table = billTableStr.split(',').map(item => parseInt(item.trim()) || 0);
        } else {
            formData.bill_table = [];
        }
        
        const coinTableStr = document.getElementById('coin_table').value;
        if (coinTableStr) {
            formData.coin_table = coinTableStr.split(',').map(item => parseInt(item.trim()) || 0);
        } else {
            formData.coin_table = [];
        }
        
        fetch(`/api/devices/${deviceId}/config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сохранения конфигурации');
            }
            return response.json();
        })
        .then(data => {
            showMessage('Конфигурация отправлена в устройство, ожидание подтверждения...');
            // Начинаем проверять ACK
            setTimeout(checkConfigAck, 1000);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ошибка при сохранении конфигурации: ' + error.message);
        });
    }
    
    // Функция для проверки ACK сообщений
    function checkSettingsAck() {
        fetch(`/api/devices/${deviceId}/settings/ack`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        showMessage('Ожидание подтверждения от устройства...');
                        // Пытаемся проверить ACK через 5 секунд
                        setTimeout(checkSettingsAck, 5000);
                        return;
                    }
                    throw new Error('Ошибка получения подтверждения настроек');
                }
                return response.json();
            })
            .then(data => {
                if (data && data.code === 0) {
                    showMessage('✅ Устройство подтвердило получение настроек');
                } else {
                    const errorMessage = getErrorDescription(data.code);
                    showError(`⚠️ Устройство вернуло ошибку: ${errorMessage} (код ${data.code})`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message !== 'Ошибка получения подтверждения настроек') {
                    showError('Не удалось получить подтверждение от устройства');
                }
            });
    }

    // Функция для проверки ACK сообщений конфигурации
    function checkConfigAck() {
        fetch(`/api/devices/${deviceId}/config/ack`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        showMessage('Ожидание подтверждения от устройства...');
                        // Пытаемся проверить ACK через 5 секунд
                        setTimeout(checkConfigAck, 5000);
                        return;
                    }
                    throw new Error('Ошибка получения подтверждения конфигурации');
                }
                return response.json();
            })
            .then(data => {
                if (data && data.code === 0) {
                    showMessage('✅ Устройство подтвердило получение конфигурации');
                } else {
                    const errorMessage = getErrorDescription(data.code);
                    showError(`⚠️ Устройство вернуло ошибку: ${errorMessage} (код ${data.code})`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message !== 'Ошибка получения подтверждения конфигурации') {
                    showError('Не удалось получить подтверждение от устройства');
                }
            });
    }
    // Функция для заполнения формы эквайринга
    function fillAcquiringForm(data) {
        document.getElementById('monobank_api_key').value = data.monobank_api_key || '';
    }
    // Функция для проверки ACK перезагрузки
    function checkRebootAck() {
        fetch(`/api/devices/${deviceId}/reboot/ack`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        showMessage('Ожидание подтверждения перезагрузки от устройства...');
                        // Пытаемся проверить ACK через 5 секунд
                        setTimeout(checkRebootAck, 5000);
                        return;
                    }
                    throw new Error('Ошибка получения подтверждения перезагрузки');
                }
                return response.json();
            })
            .then(data => {
                if (data && data.code === 0) {
                    showMessage('✅ Устройство подтвердило получение команды перезагрузки');
                } else {
                    const errorMessage = getErrorDescription(data.code);
                    showError(`⚠️ Устройство вернуло ошибку: ${errorMessage} (код ${data.code})`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message !== 'Ошибка получения подтверждения перезагрузки') {
                    showError('Не удалось получить подтверждение перезагрузки от устройства');
                }
            });
    }
    
    // Функция для получения описания ошибки по коду
    function getErrorDescription(code) {
        const errorCodes = {
            0: 'Успешно',
            100: 'Внутренняя ошибка устройства',
            101: 'Неверный запрос',
            102: 'Некорректный формат данных',
            103: 'Недопустимое значение параметра',
            104: 'Устройство занято',
            105: 'Таймаут операции',
            106: 'Недостаточно памяти',
            107: 'Ошибка доступа',
            108: 'Функция не поддерживается',
            109: 'Ошибка связи',
            110: 'Ошибка конфигурации'
        };
        
        return errorCodes[code] || 'Неизвестная ошибка';
    }
    
    // Функции вспомогательные
    function showMessage(message) {
        const messageEl = document.getElementById('success-message');
        messageEl.textContent = message;
        messageEl.classList.remove('d-none');
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            messageEl.classList.add('d-none');
        }, 5000);
    }
    
    function showError(message) {
        const errorEl = document.getElementById('state-error');
        errorEl.textContent = message;
        errorEl.classList.remove('d-none');
    }
    
    function hideError() {
        document.getElementById('state-error').classList.add('d-none');
    }
    
    function formatMoney(kopecks) {
        if (kopecks === undefined || kopecks === null) return 'Нет данных';
        return (kopecks / 100).toFixed(2) + ' UAH';
    }
    
    function formatLiters(centiliters) {
        if (centiliters === undefined || centiliters === null) return 'Нет данных';
        return (centiliters / 100).toFixed(2) + ' л';
    }
    
    function formatDateTime(dateTimeStr) {
        // Преобразование строки даты/времени в формат для отображения
        if (!dateTimeStr) return 'Нет данных';
        return dateTimeStr.replace('T', ' ');
    }
    
    function translateOperatingMode(mode) {
        const modes = {
            'WAIT': 'Ожидание',
            'BLOCK': 'Автомат заблокирован',
            'INCASS': 'Инкассация',
            'SERVIS': 'Сервисный режим',
            'SPILL': 'Пролив воды',
            'CALIBRATION': 'Калибровка',
            'SALEMONEY': 'Продажа за наличные',
            'PAYPASS': 'Оплата PayPass',
            'SALECARD': 'Продажа по карте',
            'STARTTEST': 'Проверка при старте'
        };
        return modes[mode] || mode || 'Неизвестно';
    }
    
    function getBadgeHtml(value) {
        if (value === undefined || value === null) {
            return '<span class="badge badge-secondary">Неизвестно</span>';
        }
        return value ? 
            '<span class="badge badge-success">Активен</span>' : 
            '<span class="badge badge-secondary">Неактивен</span>';
    }
    
    // Запрос данных о состоянии каждые 5 секунд
    getDeviceState(); // Первый запрос сразу при загрузке страницы
    setInterval(getDeviceState, 5000);
    
    // Обработчики кнопок
    document.getElementById('btn-request-settings').addEventListener('click', requestDeviceSettings);
    document.getElementById('btn-save-settings').addEventListener('click', saveSettings);
    document.getElementById('btn-request-config').addEventListener('click', requestDeviceConfig);
    document.getElementById('btn-save-config').addEventListener('click', saveConfig);
    
    document.getElementById('btn-reboot').addEventListener('click', function() {
        const delay = prompt('Введите задержку перезагрузки (мс):', '400');
        if (delay !== null) {
            fetch(`/api/devices/${deviceId}/reboot`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ delay: parseInt(delay) || 400 }),
            })
            .then(response => response.json())
            .then(data => {
                showMessage('Команда перезагрузки отправлена, ожидание подтверждения...');
                // Начинаем проверять ACK перезагрузки
                setTimeout(checkRebootAck, 1000);
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Ошибка при отправке команды перезагрузки: ' + error.message);
            });
        }
    });
    
    // Обработчики для вкладки "Управление"
    document.getElementById('btn-request-display').addEventListener('click', requestDisplayInfo);
    document.getElementById('btn-send-qrcode').addEventListener('click', sendQRCodePayment);
    document.getElementById('btn-send-free').addEventListener('click', sendFreePayment);
    document.getElementById('btn-clear-payment').addEventListener('click', clearPayment);
    document.getElementById('btn-pour-start-1').addEventListener('click', () => sendActionCommand('Start_1', null));
    document.getElementById('btn-pour-start-2').addEventListener('click', () => sendActionCommand('Start_2', null));
    document.getElementById('btn-pour-stop').addEventListener('click', () => sendActionCommand('Stop', null));
    document.getElementById('btn-block-on').addEventListener('click', () => sendActionCommand(null, true));
    document.getElementById('btn-block-off').addEventListener('click', () => sendActionCommand(null, false));

    // Функция для запроса информации с дисплея
    function requestDisplayInfo() {
        document.getElementById('display-info').classList.add('d-none');
        document.getElementById('display-loading').classList.remove('d-none');
        
        fetch(`/api/devices/${deviceId}/display/request`)
            .then(response => response.json())
            .then(data => {
                showMessage('Запрос информации с дисплея отправлен. Ожидание ответа...');
                
                // Ждем несколько секунд и пытаемся получить данные
                setTimeout(() => {
                    getDisplayInfo();
                }, 3000);
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Ошибка при запросе информации с дисплея: ' + error.message);
            });
    }

    // Функция для получения информации с дисплея
    function getDisplayInfo() {
        fetch(`/api/devices/${deviceId}/display`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        showError('Устройство не ответило. Попробуйте запросить информацию снова.');
                        return;
                    }
                    throw new Error('Ошибка получения информации с дисплея');
                }
                return response.json();
            })
            .then(data => {
                if (data) {
                    document.getElementById('display-loading').classList.add('d-none');
                    document.getElementById('display-info').classList.remove('d-none');
                    
                    document.getElementById('display-line-1').textContent = data.line_1 || '-';
                    document.getElementById('display-line-2').textContent = data.line_2 || '-';
                    
                    showMessage('Информация с дисплея успешно получена');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Ошибка при получении информации с дисплея: ' + error.message);
            });
    }

    // Функция для отправки QR-code платежа
    function sendQRCodePayment() {
        const orderId = document.getElementById('qrcode-order-id').value || `order_${Date.now()}`;
        const amount = parseInt(document.getElementById('qrcode-amount').value) || 0;
        
        if (amount <= 0) {
            showError('Пожалуйста, введите корректную сумму платежа');
            return;
        }
        
        fetch(`/api/devices/${deviceId}/payment/qrcode`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                order_id: orderId,
                amount: amount
            }),
        })
        .then(response => response.json())
        .then(data => {
            showMessage(`QR-code платеж отправлен: ${amount} коп., ID заказа: ${orderId}`);
            // Начинаем проверять ACK платежа
            setTimeout(checkPaymentAck, 1000);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ошибка при отправке QR-code платежа: ' + error.message);
        });
    }

    // Функция для отправки свободного начисления
    function sendFreePayment() {
        const amount = parseInt(document.getElementById('free-amount').value) || 0;
        
        if (amount <= 0) {
            showError('Пожалуйста, введите корректную сумму начисления');
            return;
        }
        
        fetch(`/api/devices/${deviceId}/payment/free`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: amount
            }),
        })
        .then(response => response.json())
        .then(data => {
            showMessage(`Свободное начисление отправлено: ${amount} коп.`);
            // Начинаем проверять ACK платежа
            setTimeout(checkPaymentAck, 1000);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ошибка при отправке свободного начисления: ' + error.message);
        });
    }

    // Функция для обнуления платежей
    function clearPayment() {
        const clearOptions = {
            CoinClear: document.getElementById('clear-coin').checked,
            BillClear: document.getElementById('clear-bill').checked,
            PrevClear: document.getElementById('clear-prev').checked,
            FreeClear: document.getElementById('clear-free').checked,
            QRcodeClear: document.getElementById('clear-qrcode').checked,
            PayPassClear: document.getElementById('clear-paypass').checked
        };
        
        fetch(`/api/devices/${deviceId}/payment/clear`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(clearOptions),
        })
        .then(response => response.json())
        .then(data => {
            showMessage('Команда обнуления платежей отправлена');
            // Начинаем проверять ACK платежа
            setTimeout(checkPaymentAck, 1000);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ошибка при обнулении платежей: ' + error.message);
        });
    }

    // Функция для отправки команды действия (пролив/блокировка)
    function sendActionCommand(pour, blocking) {
        const actionData = {};
        
        if (pour) {
            actionData.pour = pour;
        }
        
        if (blocking !== null) {
            actionData.blocking = blocking;
        }
        
        fetch(`/api/devices/${deviceId}/action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(actionData),
        })
        .then(response => response.json())
        .then(data => {
            let actionMessage = '';
            if (pour === 'Start_1') {
                actionMessage = 'Команда на включение пролива воды 1 отправлена';
            } else if (pour === 'Start_2') {
                actionMessage = 'Команда на включение пролива воды 2 отправлена';
            } else if (pour === 'Stop') {
                actionMessage = 'Команда на остановку пролива отправлена';
            } else if (blocking === true) {
                actionMessage = 'Команда на блокировку устройства отправлена';
            } else if (blocking === false) {
                actionMessage = 'Команда на разблокировку устройства отправлена';
            }
            
            showMessage(actionMessage);
            // Начинаем проверять ACK действия
            setTimeout(checkActionAck, 1000);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ошибка при отправке команды: ' + error.message);
        });
    }

    // Функция для проверки ACK действий
    function checkActionAck() {
        fetch(`/api/devices/${deviceId}/action/ack`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        showMessage('Ожидание подтверждения действия от устройства...');
                        // Пытаемся проверить ACK через 3 секунды
                        setTimeout(checkActionAck, 3000);
                        return;
                    }
                    throw new Error('Ошибка получения подтверждения действия');
                }
                return response.json();
            })
            .then(data => {
                if (data && data.code === 0) {
                    showMessage('✅ Устройство подтвердило получение команды');
                } else {
                    const errorMessage = getErrorDescription(data.code);
                    showError(`⚠️ Устройство вернуло ошибку: ${errorMessage} (код ${data.code})`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message !== 'Ошибка получения подтверждения действия') {
                    showError('Не удалось получить подтверждение действия от устройства');
                }
            });
    }

    // Функция для проверки ACK платежей
    function checkPaymentAck() {
        fetch(`/api/devices/${deviceId}/payment/ack`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        showMessage('Ожидание подтверждения платежа от устройства...');
                        // Пытаемся проверить ACK через 3 секунды
                        setTimeout(checkPaymentAck, 3000);
                        return;
                    }
                    throw new Error('Ошибка получения подтверждения платежа');
                }
                return response.json();
            })
            .then(data => {
                if (data && data.code === 0) {
                    showMessage('✅ Устройство подтвердило получение платежа');
                } else {
                    const errorMessage = getErrorDescription(data.code);
                    showError(`⚠️ Устройство вернуло ошибку: ${errorMessage} (код ${data.code})`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message !== 'Ошибка получения подтверждения платежа') {
                    showError('Не удалось получить подтверждение платежа от устройства');
                }
            });
    }
});