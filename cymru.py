import socket

def whoare(ips):
    addr = ('whois.cymru.com', '43')
    sock = socket.create_connection(addr)
    query = 'begin\ncountrycode\nasnumber\nasname\nregistry\n[insert]end\n'
    ips_on_wire = ''
    for ip in ips:
        ips_on_wire = ips_on_wire + ip + '\n'

    query = query.replace('[insert]', ips_on_wire)
    sent = 0
    while not sent == len(query):
        sendbytes = sock.send(query[sent:])
        sent += sendbytes

    data = ''
    more = True
    while more:
        more = sock.recv(8192)
        data += more

    sock.close()
    return dict(map(lambda x: (x.split('|')[1].strip(), [x.split('|')[0].strip(),
      x.split('|')[2].strip(),
      x.split('|')[4].strip(),
      x.split('|')[3].strip()]), filter(lambda x: '|' in x, data.split('\n'))))