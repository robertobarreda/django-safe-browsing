from django.test import TestCase
from safebrowsing.vendors.google import client
from safebrowsing.vendors.google import expression
from . import util

class GSB_ClientTestCase(TestCase):
    def test_parse_full_hash_response(self):
        """Full Hashes in response are properly parsed"""
        raw = "foobar:20:10\n0123456789"
        expected = {
            {
                'listname': 'foobar',
                'add_chunk_num': 20,
                'hash': utils.bin2hex('0123456789')
            }
        }
        a = client.parseFullhashResponse(raw)
        self.assertEqual(expected, a)

        expected = {
            {
                'listname': 'foobar',
                'add_chunk_num': 20,
                'hash': utils.bin2hex('0123456789')
            },
            {
                'listname': 'dingbat',
                'add_chunk_num': 30,
                'hash': utils.bin2hex('123456789')
            }
        }

        raw = "foobar:20:10\n0123456789dingbat:30:9\n123456789"
        a = client.parseFullhashResponse(raw)
        self.assertEqual(expected, a)


class GSB_UpdaterTests extends PHPUnit_Framework_TestCase {

    # def test_DownloadParse(self):
    #     raw = ('n:1858\n'
    #            'i:goog-malware-shavar\n'
    #            'u:safebrowsing-cache.google.com/safebrowsing/rd/1\n'
    #            'u:safebrowsing-cache.google.com/safebrowsing/rd/2\n')
    #     result = utils.parseDownloadResponse(raw)

    def test_Network2Int(self):
        str = "\0\0\0\0"
        val = utils.network2int(str)
        self.assertEqual(0, val)

        str = "\0\0\0\1"
        val = utils.network2int(str)
        self.assertEqual(1, val)

        str = "\1\0\0\0"
        val = utils.network2int(str)
        self.assertEqual(16777216, val)

        # now test failure case
        str = "\0\0\0"
        with self.assertRaises(GSB_Exception):
            val = utils.network2int(str)

    def test_ListToRange(self):
        vals = (1,2,3,5,6,8,10,12)
        str = utils.list2range(vals)
        self.assertEqual("1-3,5-6,8,10,12", str)

        vals = (1,2,3,4)
        str = utils.list2range(vals)
        self.assertEqual("1-4", str)

        vals = (1,3,5,7)
        str = utils.list2range(vals)
        self.assertEqual('1,3,5,7', str)

        vals = (1,)
        str = utils.list2range(vals)
        self.assertEqual('1', str)

    def test_RangeToList(self):
        s = '93865-93932'
        expected = (
            (93865, 93932),
        )
        a = utils.range2list(s)
        self.assertEqual(expected, a)

        s = '1-3,5-6,9,11'
        expected = (
            (1,3),
            (5,6),
            (9,9),
            (11,11),
        )
        a = utils.range2list(s)
        self.assertEqual(expected, a)


        s = '1'
        expected = (
            (1,1),
        )
        a = utils.range2list(s)
        self.assertEqual(expected, a)
