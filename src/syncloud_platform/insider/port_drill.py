import time

from syncloud_app import logger

from syncloud_platform.insider.config import Port
from syncloud_platform.insider.manual import ManualPortMapper
from syncloud_platform.insider.port_prober import PortProber
from syncloud_platform.insider.util import port_to_protocol, is_web_port


class PortDrill:
    def __init__(self, port_config, port_mapper, port_prober):
        self.port_prober = port_prober
        self.logger = logger.get_logger('PortDrill')
        self.port_config = port_config
        self.port_mapper = port_mapper

    def remove_all(self):
        for mapping in self.list():
            self.remove(mapping.local_port, mapping.protocol)
        self.port_config.remove_all()

    def get(self, local_port, protocol):
        return self.port_config.get(local_port, protocol)

    def list(self):
        return self.port_config.load()

    def external_ip(self):
        return self.port_mapper.external_ip()

    def remove(self, local_port, protocol):
        mapping = self.port_config.get(local_port, protocol)
        if mapping:
            self.port_mapper.remove_mapping(mapping.local_port, mapping.external_port, protocol)
            self.port_config.remove(local_port, protocol)

    def sync_one_mapping(self, local_port, protocol):

        self.logger.info('Sync one mapping: {0}'.format(local_port))
        port_to_try = local_port
        lower_limit = 10000
        found_external_port = None
        retries = 10
        for i in range(1, retries):
            self.logger.info('Trying {0}'.format(port_to_try))
            external_port = self.port_mapper.add_mapping(local_port, port_to_try, protocol)
            if not is_web_port(local_port):
                self.logger.info('not probing non http(s) ports')
                found_external_port = external_port
                break
            if self.port_prober.probe_port(external_port, port_to_protocol(local_port)):
                found_external_port = external_port
                break
            self.port_mapper.remove_mapping(local_port, external_port, protocol)

            if port_to_try == local_port:
                port_to_try = lower_limit
            else:
                port_to_try = external_port + 1

        if not found_external_port:
            raise Exception('Unable to verify open ports, tried {0} times'.format(retries))

        mapping = Port(local_port, found_external_port, protocol)
        self.port_config.add_or_update(mapping)

    def sync_new_port(self, local_port, protocol):
        self.sync_one_mapping(local_port, protocol)

    def sync(self):
        for mapping in self.list():
            self.sync_one_mapping(mapping.local_port, mapping.protocol)

    def available(self):
        return self.port_mapper is not None


class NonePortDrill:
    def __init__(self):
        self.logger = logger.get_logger('NonePortDrill')

    def remove_all(self):
        pass

    def get(self, local_port, protocol):
        return Port(local_port, None, protocol)

    def list(self):
        return []

    def external_ip(self):
        return None

    def remove(self, local_port, protocol):
        pass

    def sync_one_mapping(self, local_port, protocol):
        pass

    def sync_new_port(self, local_port, protocol):
        self.logger.info('port drill is not enabled, not adding {0} {1} mapping'.format(local_port, protocol))

    def sync(self):
        pass

    def available(self):
        return False


class PortDrillFactory:
    def __init__(self, user_platform_config, port_config, port_mapper_factory):
        self.port_config = port_config
        self.user_platform_config = user_platform_config
        self.port_mapper_factory = port_mapper_factory

    def get_drill(self, upnp_enabled, external_access, manual_public_ip, manual_public_port):
        if not external_access:
            return NonePortDrill()
        drill = None
        if upnp_enabled:
            mapper = self.port_mapper_factory.provide_mapper()
        else:
            mapper = ManualPortMapper(manual_public_ip, manual_public_port)

        if mapper:
            prober = PortProber(
                self.user_platform_config.get_redirect_api_url(),
                self.user_platform_config.get_domain_update_token())
            drill = PortDrill(self.port_config, mapper, prober)
        return drill

