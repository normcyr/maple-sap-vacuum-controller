# Maple Sap Vacuum Controller

The idea behind this hardware is to control the actuation of two solenoid valves and the operation of a diaphragm pump, based on environmental data measured by temperature, humidity and barometric sensors.

## Hardware

### Bill of material

| Item                                                                                                                  | Quantity | Price (CAD) |
| --------------------------------------------------------------------------------------------------------------------- | -------- | ----------- |
| [LM2596 DC-DC step-down power supply regulator module](https://www.aliexpress.com/item/32652456838.html)              | 1        | 0,90 $      |
| [BMP280 Digital barometric pressure sensor](https://www.aliexpress.com/item/32228095913.html)                         | 1        | 0,55 $      |
| [20x4 LCD screen with I2C](https://www.aliexpress.com/item/32704155771.html)                                          | 1        | 4,55 $      |
| [Vacuum manometer 1/4" NPT](https://www.aliexpress.com/item/4000108345570.html)                                       | 1        | 2,72 $      |
| [Dual row barrier screw terminal block wire connector, 8 positions](https://www.aliexpress.com/item/32825805597.html) | 3        | 1,67 $      |
| [Indicator signal lamp, 22mm green](https://www.aliexpress.com/item/32619257752.html)                                 | 2        | 1,02 $      |
| [Digital voltage current meter gauge](https://www.aliexpress.com/item/32707295050.html)                               | 1        | 2,78 $      |
| [Relay module, 5V](https://www.aliexpress.com/item/1005002867727977.html)                                             | 1        | 0,77 $      |
| [Selector rotary knob, latching, 1NO 1NC](https://www.aliexpress.com/item/4001332592443.html)                         | 2        | 2,05 $      |
| [Glass fuse holder, 5x20mm](https://www.aliexpress.com/item/32864552400.html)                                         | 1        | 0,37 $      |
| [WeMos D1 mini v3.0](https://www.aliexpress.com/item/32831353752.html)                                                | 1        | 2,48 $      |
| [Solenoid valve, 12V, 1/2" NPT, NO](https://www.aliexpress.com/item/1005004329739726.html)                            | 1        | 6,46 $      |
| [Solenoid valve, 12V, 1/2" NPT, NC](https://www.aliexpress.com/item/1005004329739726.html)                            | 1        | 5,71 $      |
| [SHURflo 4008-101-A65 pump, 12V](https://amzn.to/3GDoomJ)                                                             | 1        | 134,99 $    |
| [SHURflo 255-313 classic series twist-on strainer, 1/2" NPT](https://amzn.to/3WMiMMD)                                 | 1        | 23,49 $     |
| [LEDMO AC/DC power supply adapter, 12V 10A](https://amzn.to/3ClZq8X)                                                  | 1        | 19,19 $     |
| [Fuse, 8A fast acting, 5x20mm](https://www.aliexpress.com/item/32866123782.html)                                      | 1        | 0,04 $      |
| Project box                                                                                                           | 1        | 1,99 $      |
| 10AWG wire                                                                                                            |          |             |
| 16AWG wire                                                                                                            |          |             |

### Construction

Coming soon.

## Software

### How to install the software

0. Clone the repository to your local system

`git clone https://github.com/normcyr/maple-sap-vacuum-controller.git`

1. Modify the configuration file to match your system

A default configuration file is provided but at least need to be renamed in order to be used.

```bash
cp config.py.example config.py
```

Modify the value of the variables in `config.py` to match your requirements.

2. Copy the files to the ESP8266 controller

The required files should be copied to the controller file system:

```bash
cp BME280.py  \
   boot.py    \
   config.py  \
   i2c_lcd.py \
   lcd_api.py \
   main.py    \
   /pyboard/
```

### Testing with InfluxDB

It is possible to optionaly write the environmental data measured by the sensors to an InfluxDB server. The variable `SEND_DATA_INFLUXDB` in `config.py` has to be set to `True`. Once properly parametrized, the Maple Sap Vacuum Controller should be able to write the data through the Wifi network to your InfluxDB server assuming you have one running on your local network.

This goes beyond the scope of this guide and more information can be found the [website of InfluxDB](https://docs.influxdata.com/influxdb/v2.6/get-started/). This can be minimally done using the [Compose plugin](https://docs.docker.com/compose/install/#scenario-two-install-the-compose-plugin) of Docker. This will run a local InfluxDB server and it will be possible to test it with random data generated by a specific module.

1. Start the InfluxDB server

```bash
docker-compose pull
docker-compose up -d
```

2. Generate an API token to write data

Go to `http://localhost:8086` and use the credentials from `influxdb.env` to log in. In `Load Data > API tokens`, click on `Generate an API token` and select the `Custom API token` to create a new one with Read and Write permissions on the `vacuum_pump` bucket. Copy the generated token to your `config.py` file and replace the value assigned to the `INFLUXDB_TOKEN` variable with the newly generated token.

The microcontroller will now be able to send POST requests to the InfluxDB server with the environmental data measured, using the line protocol and the API /write endpoint, [as defined by InfluxDB](https://docs.influxdata.com/influxdb/v2.6/write-data/developer-tools/api/).

3. Test if your setup can connect and write to your InfluxDB instance

Once you have a configured and properly running InfluxDB instance, you can test it with the `test_infludb.py` module.

```bash
python test_influxdb.py
```

It will generate random environmental data and print the data that is posted to your InfluxDB instance. The output should look like this:

`cabane_a_sucre,sensor_id=env_inside_box temperature=1,humidity=91,pressure=1008,pump_started=True 1672707057`

A successful POST request will output a 204 HTTP code. You can also check if the data was properly written by going to the `Data Explorer` section of the InfluxDB web service.

Note that you will need the Python `requests` module installed. You can do so by running the command `pip install -u requests`.
