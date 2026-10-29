"""Real Core harness; synthetic ConfigEntries, no server/frontend boot."""
import asyncio
import json
import os
from pathlib import Path
from types import MappingProxyType

import pytest
from homeassistant import config_entries, loader
from homeassistant.components.persistent_notification.helpers import (
    _async_get_or_create_notifications, async_register_callback,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er, label_registry as lr, frame
from homeassistant.helpers.data_entry_flow import _BaseFlowManagerView
from custom_components.template_entity_checker.const import DOMAIN
from custom_components.template_entity_checker.template_sources import (
    TEMPLATE_FIELDS_BY_TYPE, _NESTED_TEMPLATE_FIELDS_BY_TYPE, _sources_from_entry,
)
from homeassistant.components.template import config_flow as template_flow
from homeassistant.helpers.selector import TemplateSelector

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ['BETA_EVIDENCE'])
DATA = {'scan_interval': 1, 'notifications': True, 'ignored_entities': []}

@pytest.fixture
async def hass(tmp_path):
    h = HomeAssistant(str(tmp_path))
    h.config.time_zone = 'UTC'
    h.config.language = 'en'
    h.config.skip_pip = True
    (tmp_path / 'custom_components').symlink_to(ROOT / 'custom_components', target_is_directory=True)
    loader.async_setup(h)
    frame.async_setup(h)
    h.config_entries = config_entries.ConfigEntries(h, {})
    await h.config_entries.async_initialize()
    dr.async_setup(h)
    await dr.async_load(h)
    await er.async_load(h)
    await lr.async_load(h)
    # Dependencies not booted: no HTTP/frontend or actual template rendering.
    h.config.components.update({'template', 'persistent_notification'})
    yield h
    await h.async_stop(force=True)
    await h.async_block_till_done()

def entry(domain=DOMAIN, options=None, **extra):
    return config_entries.ConfigEntry(domain=domain, title='Beta', data=DATA if domain==DOMAIN else {}, options=options or {}, source='user', version=2, minor_version=1, unique_id=None, discovery_keys=MappingProxyType({}), subentries_data=None, **extra)

async def seed(hass):
    for kind in ('sensor', 'climate', 'media_player', 'water_heater'):
        options = {'template_type': kind, **{f: "{{ states('sensor.beta_missing') }}" for f in TEMPLATE_FIELDS_BY_TYPE[kind]}, 'additional_options': {'availability': "{{ has_value('sensor.beta_missing') }}"}}
        if kind == 'water_heater':
            options['additional_options']['away_mode'] = "{{ states('sensor.beta_missing') }}"
        await hass.config_entries.async_add(entry('template', options, disabled_by=config_entries.ConfigEntryDisabler.USER))

def serialize(result):
    output = _BaseFlowManagerView(None)._prepare_result_json(result)
    json.dumps(output)
    return {x['name']: x for x in output['data_schema']}

async def test_flow_probatio_options_reload(hass):
    import probatio
    import voluptuous
    assert voluptuous.Schema is probatio.Schema
    a = lr.async_get(hass).async_create('A')
    b = lr.async_get(hass).async_create('B')
    result = await hass.config_entries.flow.async_init(DOMAIN, context={'source':'user'})
    fields = serialize(result)
    (OUT/'config-fields.json').write_text(json.dumps(fields, indent=2))
    assert fields['notifications']['selector'] == {'boolean': {}}
    assert fields['ignored_entities']['selector']['select']['custom_value']
    assert fields['ignored_helper_label']['selector']['select']['multiple']
    assert not fields['ignored_helper_label']['selector']['select']['custom_value']
    for value in (0, 1441, 'bad'):
        with pytest.raises(probatio.Invalid):
            result['data_schema']({**DATA, 'scan_interval':value})
    bad = await hass.config_entries.flow.async_configure(result['flow_id'], {**DATA,'ignored_entities':['bad id']})
    assert bad['errors']['ignored_entities']=='invalid_entity_id'
    serialize(bad)
    bad = await hass.config_entries.flow.async_configure(result['flow_id'], {**DATA,'ignored_helper_label':[a.label_id,b.label_id]})
    assert bad['errors']['ignored_helper_label']=='single_label_only'
    created = await hass.config_entries.flow.async_configure(result['flow_id'], {**DATA,'ignored_helper_label':[a.label_id]})
    await hass.async_block_till_done()
    e=created['result']
    assert e.state is config_entries.ConfigEntryState.LOADED
    assert e.data['ignored_helper_label']==a.label_id
    old=hass.data[DOMAIN][e.entry_id]
    result=await hass.config_entries.options.async_init(e.entry_id)
    fields=serialize(result)
    (OUT/'options-fields.json').write_text(json.dumps(fields,indent=2))
    assert fields['ignored_helper_label']['description']['suggested_value']==[a.label_id]
    saved=await hass.config_entries.options.async_configure(result['flow_id'], {'scan_interval':1,'notifications':True})
    assert saved['type']=='create_entry'
    await hass.async_block_till_done()
    assert e.options['ignored_entities']==[]
    assert e.options['ignored_helper_label']==''
    assert hass.data[DOMAIN][e.entry_id] is not old
    duplicate=await hass.config_entries.flow.async_init(DOMAIN,context={'source':'user'})
    assert duplicate['reason']=='single_instance_allowed'

async def test_startup_scan_notifications_reload_unload(hass):
    await seed(hass)
    events=[]
    remove=async_register_callback(hass,lambda kind,data:events.append(str(kind)))
    e=entry()
    await hass.config_entries.async_add(e)
    assert e.state is config_entries.ConfigEntryState.LOADED
    c=hass.data[DOMAIN][e.entry_id]
    assert c.data is None and c.update_interval is None
    await hass.async_start()
    await hass.async_block_till_done()
    assert c.data['complete'] and not c.data['load_errors']
    assert set(c.data['template_types_scanned'])=={'sensor','climate','media_player','water_heater'}
    assert set(c.data['missing_entities'])=={'sensor.beta_missing'}
    assert hass.states.get('sensor.template_entity_checker').state=='1'
    assert len(_async_get_or_create_notifications(hass))==1
    await asyncio.gather(*(hass.services.async_call(DOMAIN,'scan_now',{},blocking=True) for _ in range(3)))
    assert events==['added']
    # Real invalid future entry produces partial_error and preserves notification.
    bad=entry('template',{'template_type':'future'},disabled_by=config_entries.ConfigEntryDisabler.USER)
    await hass.config_entries.async_add(bad)
    await asyncio.sleep(11)  # Core request-refresh debounce, no replaced methods.
    await hass.services.async_call(DOMAIN,'scan_now',{},blocking=True)
    assert not c.data['complete'] and c.data['status']=='partial_error'
    assert events==['added']
    await hass.config_entries.async_remove(bad.entry_id)
    hass.states.async_set('sensor.beta_missing','1')
    await asyncio.sleep(11)
    await hass.services.async_call(DOMAIN,'scan_now',{},blocking=True)
    await hass.async_block_till_done()
    assert not _async_get_or_create_notifications(hass)
    assert c.data['complete'] and not c.data['missing_entities']
    assert await hass.config_entries.async_reload(e.entry_id)
    await hass.async_block_till_done()
    new=hass.data[DOMAIN][e.entry_id]
    assert new is not c and new.data['complete']
    assert c._unsub_refresh is None
    assert await hass.config_entries.async_unload(e.entry_id)
    assert e.entry_id not in hass.data[DOMAIN]
    assert new._unsub_refresh is None
    # Existing service intentionally remains registered and reports not_loaded.
    from homeassistant.exceptions import HomeAssistantError
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN,'scan_now',{},blocking=True)
    remove()
    assert events==['added','removed']
    (OUT/'notification-events.json').write_text(json.dumps(events))

async def test_unload_before_start(hass):
    e=entry()
    await hass.config_entries.async_add(e)
    c=hass.data[DOMAIN][e.entry_id]
    assert await hass.config_entries.async_unload(e.entry_id)
    await hass.async_start()
    await hass.async_block_till_done()
    assert c.data is None and c.update_interval is None

async def test_real_periodic_scan_and_diagnostics(hass):
    from custom_components.template_entity_checker.diagnostics import async_get_config_entry_diagnostics
    await seed(hass)
    await hass.async_start()
    e=entry()
    await hass.config_entries.async_add(e)
    await hass.async_block_till_done()
    c=hass.data[DOMAIN][e.entry_id]
    assert c.data['complete']
    first=c.data['last_scan']
    hass.states.async_set('sensor.beta_missing','1')
    await asyncio.sleep(62)  # Real coordinator timer, no time or method mocks.
    await hass.async_block_till_done()
    assert c.data['last_scan']!=first
    assert not c.data['missing_entities']
    assert hass.states.get('sensor.template_entity_checker').state=='0'
    diagnostics=await async_get_config_entry_diagnostics(hass,e)
    json.dumps(diagnostics)
    (OUT/'diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
    handle=c._unsub_refresh.__self__
    await hass.async_stop(force=True)
    await hass.async_block_till_done()
    assert handle.cancelled()


def walk(schema,prefix=''):
    result=[]
    for key,value in schema.schema.items():
        name=str(getattr(key,'schema',key))
        if isinstance(value,TemplateSelector): result.append(prefix+name)
        elif hasattr(value,'schema'):
            sub=value.schema
            if hasattr(sub,'schema'): result+=walk(sub,prefix+name+'.')
            elif isinstance(sub,dict): result+=walk(value,prefix+name+'.')
    return result

@pytest.mark.parametrize('kind', list(template_flow.TEMPLATE_TYPES))
def test_all_installed_beta_schema_fields(kind):
    actual=walk(template_flow.generate_schema(kind,'user'))
    expected=[*TEMPLATE_FIELDS_BY_TYPE[kind], 'additional_options.availability', *('additional_options.'+f for f in _NESTED_TEMPLATE_FIELDS_BY_TYPE.get(kind,()))]
    assert actual==expected
    assert template_flow.TemplateConfigFlowHandler.VERSION==2
    assert template_flow.TemplateConfigFlowHandler.MINOR_VERSION==1
    options={'template_type':kind,'additional_options':{}}
    for field in actual:
        if '.' in field: options['additional_options'][field.split('.')[1]]="{{ states('sensor.probe') }}"
        else: options[field]="{{ states('sensor.probe') }}"
    assert [s.template_field for s in _sources_from_entry(entry('template',options))]==actual
