import logging
import time
import urllib
from django.db import models, IntegrityError, transaction
from .models import GSB_Add, GSB_Sub, GSB_FullHash
from . import utils

logger = logging.getLogger('safebrowsing')


class GSB_Exception(Exception):
    pass


class GSB_Manager(models.Manager):
    timeout = 0

    def delete_all_data(self):
        """Resets the tables in the GSB schema"""
        GSB_Add.objects.all().delete()
        GSB_Sub.objects.all().delete()
        GSB_FullHash.objects.all().delete()

    def rekey(self):
        pass  # TBD

    def add_chunk_get_nums(self, list_id):
        """Fetch the chunk numbers from the database for the given list.

        @param string list_id
        @return list
        """
        chunk = 'add_chunk_num'
        return GSB_Add.objects.filter(
            list_id=list_id
        ).order_by(chunk).distinct(chunk).values_list(chunk, flat=True)

    def sub_chunk_get_nums(self, list_id):
        """Fetch the chunk numbers from the database for the given list.

        @param string list_id
        @return list
        """
        chunk = 'sub_chunk_num'
        return GSB_Sub.objects.filter(
            list_id=list_id
        ).order_by(chunk).distinct(chunk).values_list(chunk, flat=True)

    def hostkey_select_prefixes(self, host_keys):
        """Finds all prefixes the matches the host key.

        @param list[int]string|string host_keys
        @return list
        """
        # build the where clause
        if not host_keys:
            return []

        if isinstance(host_keys, (list, tuple)):
            qs = GSB_Add.objects.filter(host_key__in=host_keys)
        else:
            qs = GSB_Add.objects.filter(host_key=host_keys)


        # build the query, filter out lists that were "subtracted"
        qs = qs.filter(Q(modelbs__name=condition) | Q(modelbs__isnull=True))
        qs.filter(sub_chunk_num__isnull=True)

        list_of_unavailable_components = GSB_Sub.objects.exclude(product__in=list_of_available_products).distinct()
        list_of_available_receipts = Receipt.objects.exclude(receiptcomponent__in = list_of_unavailable_components).distinct()

        $stmt = $this->prepare(
            'SELECT a.* FROM gsb_add a '.
            'LEFT OUTER JOIN gsb_sub s '.
            ' ON s.list_id = a.list_id '.
            ' AND s.host_key = a.host_key '.
            ' AND s.add_chunk_num = a.add_chunk_num '.
            ' AND s.prefix = a.prefix '.
            $where.
            'AND s.sub_chunk_num IS NULL')

        return (array) $stmt->fetchAll(PDO::FETCH_ASSOC)

    def add_insert(self, list_id, add_chunk_num, host_key='', prefix=''):
        try:
            GSB_Add.objects.create(
                list_id=list_id,
                add_chunk_num=add_chunk_num,
                host_key=host_key,
                prefix=prefix,
            )
        except IntegrityError:
            pass

    def add_empty(self, list_id, add_chunk_num):
        self.add_insert(list_id, add_chunk_num)

    def add_delete(self, list_id, min_add_chunk_num, max_add_chunk_name):
        GSB_Add.objects.filter(
            list_id=list_id,
            add_chunk_num__range=(min_add_chunk_name, max_add_chunk_num),
        ).delete()
        GSB_Sub.objects.filter(
            list_id=list_id,
            add_chunk_num__range=(min_add_chunk_name, max_add_chunk_num),
        ).delete()
        GSB_FullHash.objects.filter(
            list_id=list_id,
            add_chunk_num__range=(min_add_chunk_name, max_add_chunk_num),
        ).delete()

    def sub_insert(self, list_id, add_chunk_num, sub_chunk_num,
                   host_key='', prefix=''):
        try:
            GSB_Sub.objects.create(
                list_id=list_id,
                add_chunk_num=add_chunk_num,
                sub_chunk_num=sub_chunk_num,
                host_key=host_key,
                prefix=prefix,
            )
        except IntegrityError:
            pass

    def sub_empty(self, list_id, sub_chunk_num):
        self.sub_insert(list_id, 0, sub_chunk_num)

    def sub_delete(self, list_id, min_sub_chunk_num, max_sub_chunk_name):
        GSB_Sub.objects.filter(
            list_id=list_id,
            sub_chunk_num__range=(min_sub_chunk_name, max_sub_chunk_num),
        ).delete()

    def fullhash_delete_old(self, now=None):
        """Delete all obsolete fullhashs"""
        if now is None:
            now = time.time()
        GSB_FullHash.objects.filter(
            create_ts__lt=(now - (60 * 45))
        ).delete()

    def fullhash_insert(self, list_id, add_chunk_num, fullhash, now=None):
        """Insert or Replace full hash"""
        if now is None:
            now = time.time()
        try:
            GSB_FullHash.objects.create(
                list_id=list_id,
                add_chunk_num=add_chunk_num,
                fullhash=fullhash,
                create_ts=now)
        except IntegrityError:
            GSB_FullHash.objects.filter(
                list_id=list_id,
                add_chunk_num=add_chunk_num,
                fullhash=fullhash,
            ).update(create_ts=now)

    def fullhash_exists(self, list_id, fullhash, now=None):
        if now is None:
            now = time.time()
        return GSB_FullHash.objects.filter(
            list_id=list_id,
            fullhash=fullhash,
            create_ts__gt=now
        ).count() > 0

    def rfd_get(self):
        return GSB_rfd.objects.get(pk=1)

    def rfd_set(self, state):
        state.save()
        self.set_timeout(0)

    def set_timeout(self, timeout):
        """ This is a bit tricky. Here instead of saving data, we just
        store it locally. We'll update the gsb_rfd state table
        all at once later
        """
        self.timeout = timeout

    def get_timeout(self):
        return self.timeout

    ## Updater ---------------------------------------------------------------

    def formatted_request(list_id, adds, subs):
        """Format a full request body for a desired list including name and
        full ranges for add and sub
        """
        buildpart = ''

        if len(adds) > 0:
            buildpart += 'a:' . utils.list2range(adds)

        if len(adds) > 0 and len(subs) > 0:
            buildpart += ':';

        if len(subs) > 0:
            buildpart += 's:' + utils.list2range(subs)

        return list_id + ';' + buildpart + "\n"

    def format_download_request(self, gsb_list):
        """Reads datastore for current add and sub chunks
        and composes the proper 'download' request
        """
        return ''.join([
            self.formatted_request(
                list_id,
                self.add_chunk_get_nums(list_id),
                self.sub_chunk_get_nums(list_id)) for list_id in gsb_list])

    def parse_add_shavar_chunk(self, list_id, add_chunk_num, hashlen, raw):
        sz = len(raw)
        offset = 0
        result = []

        while offset < sz:
            hostkey = utils.bin2hex(raw[offset:offset + 4])
            offset += 4
            count = ord(raw[offset:offset + 1])
            offset += 1

            if count == 0:
                # special case, really 'hostkey, prefix'
                result.append({
                    'action': 'add_insert',
                    'list_id': list_id,
                    'add_chunk_num': add_chunk_num,
                    'host_key': hostkey,
                    'prefix': hostkey
                })
            else:
                for i in xrange(count):
                    result.append({
                        'action': 'add_insert',
                        'list_id': list_id,
                        'add_chunk_num': add_chunk_num,
                        'host_key': hostkey,
                        'prefix': utils.bin2hex(
                            raw[offset:offset + hashlen])
                    })
                    offset += hashlen

        if offset != sz:
            raise GSB_Exception(
                "Mismatch in AddShavar Chunk {0} != {1}".format(offset, sz))

        return result

    def parse_sub_shavar_chunk(self, list_id, sub_chunk_num, hashlen, raw):
        sz = len(raw)
        offset = 0
        result = []

        while offset < sz:
            hostkey = utils.bin2hex(raw[offset:offset + 4])
            offset += 4
            count = ord(raw[offset:offset + 1])
            offset += 1

            if count == 0:
                # special case where hostkey is prefix
                result.append({
                    'action': 'sub_insert',
                    'list_id': list_id,
                    'sub_chunk_num': sub_chunk_num,
                    'add_chunk_num': utils.network2int(raw[offset:offset + 4]),
                    'host_key': hostkey,
                    'prefix': hostkey
                })
                offset += 4
            else:
                for i in xrange(count):
                    result.append({
                        'action': 'sub_insert',
                        'list_id': list_id,
                        'sub_chunk_num': sub_chunk_num,
                        'add_chunk_num': utils.network2int(
                            raw[offset:offset + 4]),
                        'host_key': $hostkey,
                        'prefix': utils.bin2hex(
                            raw[offset + 4:offset + 4 + hashlen])
                    })
                    offset += 4 + hashlen

        if offset != sz:
            raise GSB_Exception(
                "Mismatch in SubShavar Chunk {0} != {1}".format(offset, sz))

    def parse_redirect_response(self, list_id, raw):
        offset = 0
        sz = len(raw)
        result = []

        while offset < sz:
            newline = raw.find("\n", offset)
            if newline == -1:
                raise GSB_Exception(
                    "Counldn't find newline with {0} {1}".format(offset sz))

            header = raw[offset:newline - offset]
            parts = header.split(':', 4)
            cmd = parts[0]
            chunk_num = int(parts[1])
            hashlen = int(parts[2])
            chunklen = int(parts[3])
            msg = raw[newline + 1:newline + 1 + chunklen]

            if cmd == 'a':
                if not msg:
                    result.append({
                        'action': 'add_empty',
                        'list_id': list_id,
                        'add_chunk_num': chunk_num
                    );
                else:
                    result.extend(
                        self.parse_add_shavar_chunk(
                            list_name, chunk_num, hashlen, msg))

            elif cmd == 's':
                if not msg:
                    result.append({
                        'action': 'sub_empty',
                        'list_id': list_id,
                        'sub_chunk_num': chunk_num
                    );
                else:
                    result.extend(
                        self.parse_sub_shavar_chunk(
                            list_name, chunk_num, hashlen, msg))

            else:
                raise GSB_Exception(
                    "Got bogus command in line %s".format(header))

            offset = newline + 1 + chunklen

        return result

    def parse_download_response(self, raw):
        """Parses the init download response, parses, convert, fetches
        redirect data and returns a stateless "list of commands" (could
        be saved/tested)
        """

        lines = raw.strip().split("\n")
        currentlist = None
        result = []

        for line in lines:
            key, value = line.split(':', 2)

            if key == 'n':
                result.append({
                    'action': 'set_timeout',
                    'timeout': int(value.strip())
                })

            elif key == 'e':
                if value == 'pleaserekey':
                    result.append({
                        'action': 'rekey'
                    })

            elif key == 'r':
                if value == 'pleasereset':
                    result.append({
                        'action': 'delete_all_data'
                    })

            elif key == 'i':
                currentlist = value

            elif key == 'u':
                if currentlist is None:
                    raise GSB_Exception(
                        "Got URL request before a list was set")

                rr = $this->request->downloadChunks('http://' . value)
                result.extend(
                    self.parse_redirect_response(currentlist, rr))

            elif key == 'ad':
                if currentlist is None:
                    raise GSB_Exception(
                        "Got URL request before a list was set")

                for interval in utils.range2list(value)
                    result.append({
                        'action': 'add_delete',
                        'list_id': currentlist,
                        'min_add_chunk_num': interval[0],
                        'max_add_chunk_num': interval[1]
                    })

            elif key == 'sd':
                if currentlist is None:
                    raise GSB_Exception(
                        "Got URL request before a list was set")

                for interval in  utils.range2list(value)
                    result.append({
                        'action': 'sub_delete',
                        'list_id': currentlist,
                        'min_sub_chunk_num': interval[0],
                        'max_sub_chunk_num': interval[1]
                    })

            else:
                # "The client MUST ignore a line starting with a
                # keyword that it doesn't understand."
                logger.warning("Unknown line in response: %s", line)


        return result

    def download_data(self, gsb_lists, force=False):
        """Main part of updater function, will call all other functions, merely
        requires the request body, it will then process and save all data as well
        as checking for ADD-DEL and SUB-DEL, runs silently so won't return
        anything on success.
        """
        start = time.time()
        logger.info("Updater woke up")

        state = self.rfd_get()
        diff = state.next_attempt - start
        if diff > 0:
            if not force:
                logger.info("Too soon. Need to wait for %d seconds", diff)
                return

            logger.info("Ignoring timeout guidance. "
                        "(should wait for %d seconds", diff)

        now = time.time()
        body = self.format_download_request(gsb_lists)
        logger.debug(
            "Computing existing chunks took %d seconds", time.time() - now)

        if not body:
            raise GSB_Exception("Missing a body for data request")

        logger.debug("Request = %s", body)

        now = time()
        raw = $this->request->download(body)

        # processes and saves all data
        commands = self.parse_download_response(raw)
        logger.info(
            "Got %d commands in %d seconds", len(commands), time() - now)

        try:
            now = time.time()
            with transaction.commit_on_success():
                for cmd in commands:
                    logger.debug("Command %s", urllib.urlencode(cmd))
                    action = cmd.pop('action')
                    getattr(self, action)(+cmd)

                # Ok we got this far, we need to update state.
                state = self.rfd_get()
                state.error_count = 0
                state.last_attempt = state.last_success = time.time()
                timeout = self.get_timeout()
                if timeout == 0:
                    timeout = 60 * 15
                state.next_attempt = time.time() + timeout
                self.rfd_set(state)

                logger.info(
                    "Processed %d entries in %d seconds. "
                    "Next update in %d seconds",
                    len(commands), time.time() - now, timeout)

        except Exception, e:
            logger.exception("Chunk update failed")
            transaction.rollback()

            with transaction.commit_on_success():
                state = self.get_rfd()
                state.last_attempt = time.time()
                state.error_count += 1
                next_attempt = {
                    1: 1,
                    2: 30,
                    3: 60,
                    4: 120,
                    5: 240,
                }.get(state.error_count, 480)
                state.next_attempt = time.time() + next_attempt * 60
                self.rfd_set(state)
                logger.info(
                    "Got %d errors, next Attempt in %d minutes",
                    state.error_count, next_attempt)

        logger.info("Update complete in %d seconds", time.time() - start)

    ## Request ---------------------------------------------------------------

    API_APPVER = '1.5.2'
    API_URL = 'http://safebrowsing.clients.google.com/safebrowsing/'
    API_CLIENT = 'api'
    API_PVER = '2.2'

    # function __construct($apikey, $mode=null, $path=null) {
    #     $this->apikey = $apikey;
    #     $this->counter = 0;

    #     $this->mode = $mode;
    #     $this->path = $path;
    # }

    # /**
    # * Retrieves the types of the GSB lists.
    # */
    # function getListTypes() {
    #     $req = $this->makeRequest('list');
    #     $result = $this->request($req, null);
    #     return $result['response'];
    # }

    # /**
    # * Downloads chunks of the GSB lists for the given list type.
    # *
    # * @param unknown_type $body
    # * @param unknown_type $followBackoff
    # */
    # function download($body, $followBackoff = false) {
    #     $req = $this->makeRequest('downloads');
    #     $result = $this->post_request($req, $body . "\n", $followBackoff);
    #     return $result['response'];
    # }

    # /**
    # * Retrieves the full hash from the GSB API.
    # *
    # * @param unknown_type $body
    # */
    # function getFullHash($body) {
    #     $req = $this->makeRequest('gethash');
    #     $result = $this->post_request($req, $body);
    #     $data = $result['response'];
    #     $httpcode = $result['info']['http_code'];
    #     if ($httpcode == 200 && !empty($data)) {
    #         return $data;
    #     } elseif ($httpcode == 204 && empty($data)) {
    #         // 204 Means no match
    #         return '';
    #     } else {
    #         throw new GSB_Exception("ERROR: Invalid response returned from GSB ($httpcode)");
    #     }
    # }

    # /**
    # * Follows the redirect URL and downloads the real chunk data.
    # *
    # * @param unknown_type $redirectUrl
    # * @param unknown_type $followBackoff
    # * @return Ambigous <multitype:mixed, multitype:mixed >
    # */
    # function downloadChunks($redirectUrl) {
    #     $result = $this->request($redirectUrl);
    #     return $result['response'];
    # }

    # /**
    # * Make a request to the GSB API from the given URL's, POST data can be
    # * passed via $options. $followBackoff indicates whether to follow backoff
    # * procedures or not
    # *
    # * @param unknown_type $url
    # * @param unknown_type $options
    # * @param unknown_type $followBackoff
    # * @return multitype:mixed
    # */
    # function request($url, $followBackoff = false) {
    #     if ($this->mode == 'replay') {
    #         $fname = sprintf("%s-%03d.php-serialized", $this->path,
    #                          $this->counter + 1, '.php-serialized');
    #         if (file_exists($fname)) {
    #             print "Replay with $fname\n";
    #             $result = unserialize(file_get_contents($fname));
    #             $this->counter++;

    #             return $result;
    #         }
    #     }

    #     $ch = curl_init();
    #     curl_setopt($ch, CURLOPT_URL, $url);
    #     curl_setopt($ch, CURLOPT_HEADER, 0);
    #     curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    #     $data = curl_exec($ch);
    #     $info = curl_getinfo($ch);
    #     curl_close($ch);

    #     if ($info['http_code'] == 400) {
    #         throw new GSB_Exception("Invalid request for $url");
    #     }

    #     if ($followBackoff && $info['http_code'] > 299) {
    #         //$this->backoff($info, $followBackoff);
    #     }

    #     $result = array('url' => $url,
    #                     'postdata' => '',
    #                     'info' => $info,
    #                     'response' => $data);

    #     if ($this->mode == 'replay') {
    #         $this->counter++;
    #         $fname = sprintf("%s-%03d.php-serialized", $this->path,
    #                          $this->counter, '.php-serialized');
    #         printf("Writing $fname\n");
    #         file_put_contents($fname, serialize($result));
    #     }
    #     return $result;
    # }

    # /**
    # * Make a request to the GSB API from the given URL's, POST data can be
    # * passed via $options. $followBackoff indicates whether to follow backoff
    # * procedures or not
    # *
    # * @param unknown_type $url
    # * @param unknown_type $options
    # * @param unknown_type $followBackoff
    # * @return multitype:mixed
    # */
    # function post_request($url, $postdata, $followBackoff = false) {
    #     if ($this->mode == 'replay') {
    #         $fname = sprintf("%s-%03d.php-serialized", $this->path,
    #                          $this->counter + 1, '.php-serialized');
    #         if (file_exists($fname)) {
    #             print "Replay with $fname\n";
    #             $result = unserialize(file_get_contents($fname));
    #             $this->counter++;
    #             return $result;
    #         }
    #     }
    #     $ch = curl_init();
    #     curl_setopt($ch, CURLOPT_URL, $url);
    #     curl_setopt($ch, CURLOPT_HEADER, 0);
    #     curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    #     curl_setopt($ch, CURLOPT_POST, true);
    #     curl_setopt($ch, CURLOPT_POSTFIELDS, $postdata);
    #     $data = curl_exec($ch);
    #     $info = curl_getinfo($ch);
    #     curl_close($ch);

    #     $httpcode = (int)$info['http_code'];
    #     switch ($httpcode) {
    #     case 204:
    #     case 200:
    #         // these are ok
    #         break;

    #     case 400:
    #         throw new GSB_Exception("400: Invalid request for $url");
    #     case 403:
    #         throw new GSB_Exception("403: Forbidden. Client id is invalid");
    #     case 503:
    #         throw new GSB_Exception("503: Backoff son.");
    #     case 505:
    #         throw new GSB_Exception("505: Bad Protocol.");
    #     default:
    #         throw new GSB_Exception("Unknown http code " . $httpcode);
    #     }

    #     $result = array('url' => $url,
    #                     'postdata' => $postdata,
    #                     'info' => $info,
    #                     'response' => $data);

    #     if ($this->mode == 'replay') {
    #         $this->counter++;
    #         $fname = sprintf("%s-%03d.php-serialized", $this->path,
    #                          $this->counter, '.php-serialized');
    #         printf("Writing $fname\n");
    #         file_put_contents($fname, serialize($result));
    #     }
    #     return $result;
    # }

    # /**
    # * Constructs a URL to the GSB API
    # */
    # function makeRequest($cmd) {
    #     $str = sprintf("%s%s?client=%s&apikey=%s&appver=%s&pver=%s",
    #                    self::API_URL,
    #                    $cmd,
    #                    self::API_CLIENT,
    #                    $this->apikey,
    #                    self::API_APPVER,
    #                    self::API_PVER);
    #     return $str;
    # }


gsb_manager = GSB_Manager()
