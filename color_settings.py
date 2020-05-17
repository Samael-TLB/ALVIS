from kivy.uix.settings import*
from kivy.uix.colorpicker import ColorPicker 
from kivy.properties import *
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.button import Button

class SettingColor(SettingItem):
    
    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it's shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    colorpicker = ObjectProperty(None)
    '''(internal) Used to store the current colorpicker from the popup and
    to listen for changes.

    :attr:`colorpicker` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''
    
    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind('on_release', self._create_popup)

    def _dismiss(self, *largs):
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
        
        self.value = str(self.colorpicker.color)[1:-1]
        
    def _create_popup(self, instance):
        # create popup layout
        content=BoxLayout(orientation='vertical', spacing='5dp')
        
        popup_width = min(0.95 * Window.width, dp(500))

                
        self.colorpicker=ColorPicker(color=list(map(float,self.value.split(','))))
        content.add_widget(self.colorpicker)
        
        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, 0.8),
            width=popup_width)
        
        # all done, open the popup !
        popup.open()
