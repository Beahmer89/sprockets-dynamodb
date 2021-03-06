import base64
import datetime
import sys
import unittest
import uuid

from sprockets_dynamodb import utils


class UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return datetime.timedelta(0)


class IsBinaryTests(unittest.TestCase):

    @unittest.skipIf(sys.version_info.major > 2, 'is_binary is Python2 only')
    def test_is_binary_true(self):
        self.assertTrue(utils.is_binary('\0x01\0x02\0x03'))

    @unittest.skipIf(sys.version_info.major > 2, 'is_binary is Python2 only')
    def test_is_binary_false(self):
        self.assertFalse(utils.is_binary('This is ASCII'))


class MarshallTests(unittest.TestCase):
    maxDiff = None

    def test_complex_document(self):
        uuid_value = uuid.uuid4()
        dt_value = datetime.datetime.utcnow().replace(tzinfo=UTC())
        value = {
            'key1': 'str',
            'key2': 10,
            'key3': {
                'sub-key1': 20,
                'sub-key2': True,
                'sub-key3': 'value'
            },
            'key4': None,
            'key5': ['one', 'two', 'three', 4, None, True],
            'key6': {'a', 'b', 'c'},
            'key7': {1, 2, 3, 4},
            'key9': uuid_value,
            'key10': b'\0x01\0x02\0x03',
            'key11': {b'\0x01\0x02\0x03', b'\0x04\0x05\0x06'},
            'key12': dt_value
        }
        expectation = {
            'key1': {'S': 'str'},
            'key2': {'N': '10'},
            'key3': {'M':
                {
                    'sub-key1': {'N': '20'},
                    'sub-key2': {'BOOL': True},
                    'sub-key3': {'S': 'value'}
                }
            },
            'key4': {'NULL': True},
            'key5': {'L': [{'S': 'one'}, {'S': 'two'}, {'S': 'three'},
                           {'N': '4'}, {'NULL': True}, {'BOOL': True}]},
            'key6': {'SS': ['a', 'b', 'c']},
            'key7': {'NS': ['1', '2', '3', '4']},
            'key9': {'S': str(uuid_value)},
            'key10': {'B': base64.b64encode(b'\0x01\0x02\0x03').decode('ascii')},
            'key11': {'BS': [base64.b64encode(b'\0x01\0x02\0x03').decode('ascii'),
                             base64.b64encode(b'\0x04\0x05\0x06').decode('ascii')]},
            'key12': {'S': dt_value.isoformat()}
        }
        self.assertDictEqual(expectation, utils.marshall(value))

    def test_value_error_raised_on_unsupported_type(self):
        self.assertRaises(ValueError, utils.marshall, {'key': self})

    def test_value_error_raised_on_mixed_set(self):
        self.assertRaises(ValueError, utils.marshall, {'key': {1, 'two', 3}})


class UnmarshallTests(unittest.TestCase):
    maxDiff = None

    def test_complex_document(self):
        uuid_value = str(uuid.uuid4())
        dt_value = datetime.datetime.utcnow()
        value = {
            'key1': {'S': 'str'},
            'key2': {'N': '10'},
            'key3': {'M':
                {
                    'sub-key1': {'N': '20'},
                    'sub-key2': {'BOOL': True},
                    'sub-key3': {'S': 'value'}
                }
            },
            'key4': {'NULL': True},
            'key5': {'L': [{'S': 'one'}, {'S': 'two'}, {'S': 'three'},
                           {'N': '4'}, {'NULL': True}, {'BOOL': True}]},
            'key6': {'SS': ['a', 'b', 'c']},
            'key7': {'NS': ['1', '2', '3', '4']},
            'key8': {'S': dt_value.isoformat()},
            'key9': {'S': uuid_value},
            'key10': {'B': base64.b64encode(b'\0x01\0x02\0x03').decode('ascii')},
            'key11': {'BS': [base64.b64encode(b'\0x01\0x02\0x03').decode('ascii'),
                             base64.b64encode(b'\0x04\0x05\0x06').decode('ascii')]}
        }
        expectation = {
            'key1': 'str',
            'key2': 10,
            'key3': {
                'sub-key1': 20,
                'sub-key2': True,
                'sub-key3': 'value'
            },
            'key4': None,
            'key5': ['one', 'two', 'three', 4, None, True],
            'key6': {'a', 'b', 'c'},
            'key7': {1, 2, 3, 4},
            'key8': dt_value.isoformat(),
            'key9': uuid_value,
            'key10': b'\0x01\0x02\0x03',
            'key11': {b'\0x01\0x02\0x03', b'\0x04\0x05\0x06'}
        }
        self.assertDictEqual(expectation, utils.unmarshall(value))

    def test_value_error_raised_on_unsupported_type(self):
        self.assertRaises(ValueError, utils.unmarshall, {'key': {'T': 1}})
