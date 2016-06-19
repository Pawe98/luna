import threading

from requests import ConnectionError

import xbmc
from resources.lib.controller.basecontroller import BaseController, route, register
from resources.lib.di.requiredfeature import RequiredFeature
from resources.lib.nvhttp.request.staticrequestservice import StaticRequestService

from resources.lib.views.main import Main


@register
class MainController(BaseController):
    def __init__(self):
        super(MainController, self).__init__()
        self.addon = RequiredFeature('addon').request()
        self.logger = RequiredFeature('logger').request()
        self.host_context_service = RequiredFeature('host-context-service').request()
        self.host_manager = RequiredFeature('host-manager').request()
        self.window = None

    @route(name="index")
    def index_action(self):
        # Manually close the spinning wheel since it gets stuck for fullscreen windows
        self.window = Main(controller=self)
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self.update_host_status()
        self.window.doModal()
        del self.window

    @route(name="host_select")
    def select_host(self, host):
        self.host_context_service.set_current_context(host)
        self.render('game_list', {'host': host})
        # window = GameList(host)
        # window.doModal()

    def add_host(self):
        host_controller = RequiredFeature('host-controller').request()
        self.logger.info("Calling host controller")
        ret_val = self.render('host_add')
        self.logger.info(ret_val)
        if ret_val:
            self.window.update()
        del host_controller

    def open_settings(self):
        self.addon.openSettings()

    def update_host_status(self):
        update_host_thread = threading.Thread(target=self._update_host_status)
        update_host_thread.start()

    def _update_host_status(self):
        import xbmcgui
        self.logger.info("Getting Host Status")
        background_dialog = xbmcgui.DialogProgressBG()
        background_dialog.create('Refreshing Host Status')
        hosts = self.host_manager.get_hosts()
        for key, host in hosts.iteritems():
            try:
                StaticRequestService.get_static_server_info(host.local_ip)
                host.state = host.STATE_ONLINE
            except ConnectionError:
                host.state = host.STATE_OFFLINE
        self.window.update_host_status(hosts.raw_dict())
        self.logger.info("Getting Host Status ... Done")
        background_dialog.close()
        del background_dialog
        return
