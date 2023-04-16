# Vestasync

Vestasync - это ПО для бекапа и восстановления контроллеров Wirenboard. Оно решает две задачи:

1. Создание бекапа конфигурации автоматически и деплой ее на удаленный git-сервер (поддерживается Gitea, для поддержки других сервисов необходимо дописать соответствующую функцию создания репозитория) по расписанию (раз в день)
2. Восстановление бекапа одной командой: после подключения нового контроллера достаточно ввести его IP и имя хоста предыдущего контроллера, чтобы Vestasync автоматически восстановила бекап вплоть до MAC-адресов сетевых интерфейсов, чтобы не было нужды менять настройки на DHCP-сервере. После перезагрузки контроллер вернется в сеть с IP старого контроллера.

## Установка

```bash
git clone https://github.com/vvzvlad/vestasync
cd vestasync
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Команды

Vestasync поддерживает три команды: `install`, `update` и `restore`. 

### install

Команда `install` выполняет подготовительные действия — устанавливает ПО, создает гит-репозитарий, устанавливает службы (подробнее в разделе "Службы").  

Пример запуска:

```bash
./vestasync.py 
--cmd install 
--device_ip 192.168.1.85 
--gitea_address http://192.168.1.101:3001/ 
--device_new_name WB2 
--gitea_token de8a2eaee0d2f27746157c2fd563815f932d670c`
```

```--cmd install```: означает, что надо установить Vestasync на контроллер и подготовить его к созданию бекапа  
```--device_ip```: IP-адрес контроллера  
```--gitea_address```: адрес Gitea-сервера, куда будет отправлен бекап в виде "http://192.168.1.101:3001/"  
```--device_new_name```: имя контроллера, из которого вместе с SN будет сформировано название контроллера, которое запишется в хостнейм и будет служить именем репозитария с конфигами  
```--gitea_token```: токен для авторизации на Gitea-сервере (получается в интерфейсе)  

### restore

Команда `restore` выполняет восстановление существующего бекапа на контроллере.

Пример запуска:

```bash
./vestasync.py 
--cmd restore 
--device_ip 192.168.98.85 
--gitea_address http://192.168.1.101:3001/ 
--gitea_token de8a2eaee0d2f27746157c2fd563815f932d670c`
--source_hostname WB2-A3TBJXLS
```

Используются те же аргументы, что и в ```install```, но дополнительно еще нужен аругмент ```source_hostname```, который определяет имя контроллера, с которого выполняется бекап. ```device_new_name``` не используетс, в качестве имени будет взято имя старого контроллера. 



## Службы
Службы, которые будут запущенны на контроллере при установке:

### Восстановление MAC-адресов (apply_macs)
Служба apply_macs отвечает за применение MAC-адресов к сетевым интерфейсам при загрузке системы. 
Эта служба считывает MAC-адреса из файлов, расположенных в каталоге /mnt/data/etc/vestasync/macs/, если они есть, и присваивает их соответствующим интерфейсам, таким как eth0, eth1, wlan0 и т. д. Это используется, если на контроллер был восстанновлен созданный бекап, чтобы сохранять MAC-адреса старого контроллера, и соотвественно, адрес, выданный DHCP. 
Для изменения MAC-адресов на изначальные надо просто удалить все файлы и перезагрузиться:  
```
rm -rf /mnt/data/etc/vestasync/macs/*
reboot
```
Или, если надо сделать это временно, остановить службу: ```systemctl stop apply_macs.service```  
Обратно запустить: ```systemctl start apply_macs.service```  
Узнать статус: ```systemctl status apply_macs.service```  

### Автоматическое версионирование и деплой конфигов (pushgit)
Служба pushgit работает в паре с таймером pushgit.timer. Они обеспечивают автоматическое сохранение конфигов в репозиторий Git на удаленном сервере ежедневно. 
Это позволяет сохранять изменения в файлах и версионировать их, что упрощает управление конфигурационными файлами и предотвращает потерю данных при их случайном изменении или удалении. 
Чтобы отключить сохранение, надо остановить службу: ```systemctl stop pushgit.timer```  
Запуск и проверка статуса аналогично предыдущей:  
Запустить: ```systemctl start pushgit.timer```  
Узнать статус: ```systemctl status pushgit.timer``` 

Для принудительной загрузки конфигов надо выполнить в консоли контроллера ```/usr/local/bin/pushgit.sh```


## Gitea
В качестве git-сервера используется gitea. Предполагается, что она работает локально, но можно использовать и публичные инсталляции. Устанавливать ее можно любым удобным способом, например с помощью такого docker-compose:
```
version: "3"

networks:
  gitea:
    external: false

services:
  server:
    image: gitea/gitea:1.19.0
    container_name: gitea
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - GITEA__database__DB_TYPE=postgres
      - GITEA__database__HOST=gitea_pg_db:5432
      - GITEA__database__NAME=gitea
      - GITEA__database__USER=gitea
      - GITEA__database__PASSWD=gitea
    restart: always
    networks:
      - gitea
    volumes:
      - /root/gitea/data:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3001:3000"
      - "222:22"
    depends_on:
      - db

  db:
    image: postgres:14
    restart: always
    container_name: gitea_pg_db
    environment:
      - POSTGRES_USER=gitea
      - POSTGRES_PASSWORD=gitea
      - POSTGRES_DB=gitea
    networks:
      - gitea
    volumes:
      - /root/gitea/pg-data:/var/lib/postgresql/data
```
