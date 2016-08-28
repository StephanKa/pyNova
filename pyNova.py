import serial
import glob
import time
import sys
import random

class NovaHeadEnumeration():
    TH = 0
    PY = 1
    NJ = 1
    
class NovaMeasurementMethod():
    POWER = 0
    ENERGY = 1
    FREQUENCY = 2
    
class NovaCommands():
    FORCE_POWER = 'FP'
    FORCE_ENERGY = 'FE'
    GET_VERSION = 'VE'
    GET_HEAD_INFO = 'HI'
    GET_INSTRUMENT_INFO = 'II'
    GET_UNIT = 'SI'
    GET_POWER = 'SP 10' # "10" is timeout in hundreds of milliseconds
    GET_ENERGY = 'SE 10' # "10" is timeout in hundreds of milliseconds
    
class NovaUnits():
    ''' Translates the unit response to wirtten out string for better understanding of measure unit '''
    UNIT_SETUP = {'A' : 'Amps', 'J' : 'Joules', 'V' : 'Volts', 'W' : 'Watts', 'L' : 'Lux', 'X' : 'No measurement yet', 'Simulation' : 'Simulation'}
    
class Error():
    ERROR_MESSAGES = {'?PARAM ERROR' : 'bad operand.', 
                    '?TIMEOUT: NO PULSE' : 'when the requested time period elapsed w/o pulse coming in',
                    '?HEAD NOT MEASURING POWER' : 'head not measure power',
                    '?NOT IN MAIN POWER SCREEN' : 'device is not in main screen',
                    '?HEAD NOT CONNECTED' : 'head is not connected to device',
                    '?UNKNOWN COMMAND' : 'unknown command'}
    
class NovaSerialDriver():

    BAUDRATES = {'300' : 4, '1200' : 5, '4800' : 6, '9600' : 1, '19200' : 2}
    ERROR_CHAR = '?'
    COMMAND_CHAR = '$'
    RESULT_CHAR = '*'

    def __init__(self, com_port='COM1', baudrate=9600):
        ''' initialize default values and needed values for the rs232 setup '''
        self.connection = None
        self.com_port = com_port
        self.baudrate = baudrate
        self.parity = serial.PARITY_NONE
        self.cts_line = True # must be true for NOVA devices

        self.dtr_rts_lines = False
        self.stop_bit = serial.STOPBITS_ONE
        self.data_bits = serial.EIGHTBITS
        self.siumulation = False
        
    def __setup_connection(self):
        ''' try to open connection with given settings '''
        try:
            self.connection = serial.Serial(port=self.com_port, 
                                        baudrate=self.baudrate,
                                        bytesize=self.data_bits,
                                        parity=self.parity,
                                        stopbits=self.stop_bit,
                                        dsrdtr=self.dtr_rts_lines,
                                        rtscts=self.cts_line)

            self.connection.flush()
            self.connection.reset_input_buffer()
            self.connection.reset_output_buffer()
        except:
            raise Exception('connection could not be established!')
        
    def open(self):
        ''' open the connection '''
        if(not self.simulate_device):
            self.__setup_connection()
        
    def close(self):
        ''' close the connection '''
        if(not self.simulate_device):
            self.connection.close()
        
    def simulate_device(self, simulation):
        ''' simulation for this device for developer to develope without any device '''
        self.simulation = simulation
        
    def __build_command_string(self, cmd):
        ''' build the command string that will be needed for the Nova devices '''
        return '{0}{1}\r\n'.format(self.COMMAND_CHAR, cmd)
        
    def __send_receive_data(self, cmd):
        ''' send the command and read the response after 0.5seconds '''
        self.connection.write(bytes(b'{0}'.format(self.__build_command_string(cmd))))
        result = ''
        # need a sleep command for stabilization of rs232 connection
        time.sleep(0.5)
        while(self.connection.inWaiting() > 0):

            result += self.connection.read(1)
        return self._extract_received_data(result).replace('\r\n', '')
        
    def _get_version(self):
        ''' get the ROM version of the measurement device '''
        if(self.simulate_device):
            return 'Simulation'
        else:
            return self.__send_receive_data(NovaCommands.GET_VERSION)
        
    def _get_head_info(self):
        ''' get informations about the connected head '''
        if(self.simulate_device):
            return 'Simulation'
        else:
            return self.__send_receive_data(NovaCommands.GET_HEAD_INFO)
        
    def _get_instrument_info(self):
        ''' get informations about the measurement device itself '''
        if(self.simulate_device):
            return 'Simulation'
        else:
            return self.__send_receive_data(NovaCommands.GET_INSTRUMENT_INFO)
        
    def _get_unit(self):
        ''' get the unit of the measurement method '''
        if(self.simulate_device):
            return 'Simulation'
        else:
            return self.__send_receive_data(NovaCommands.GET_UNIT)
    
    def _extract_received_data(self, data):
        ''' extract the delivered answer in results or error messages '''
        if(self.RESULT_CHAR in data):
            return data[1:]
        elif(self.ERROR_CHAR in data):
            return Error.ERROR_MESSAGES[data]
        else:
            raise Exception('returned string has not the defined characters in it!')
        
    def _format_numeric_value(self, value_string):
        ''' convert the given scientific value to more readable number '''
        return float(value_string)
        
    def get_infos(self):
        ''' collect all infos and return a dictionary to the user '''
        temp_dict = {}
        temp_dict['ROM Version'] = self._get_version()
        temp_dict['Head Info'] = self._get_head_info()
        temp_dict['Instrument Info'] = self._get_instrument_info()
        temp_dict['Unit'] = NovaUnits.UNIT_SETUP[self._get_unit()]
        return temp_dict

    def get_power(self):
        ''' get the current value from device'''
        if(self.simulate_device):
            return random.random()
        else:
            return self._format_numeric_value(self.__send_receive_data(NovaCommands.GET_POWER))
        
    def serial_ports(self):
        ''' Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        '''
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
