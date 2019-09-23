from . import XMLRenderer
from .vosi import CapabilitiesRendererMixin, TablesetRendererMixin


class VoresourceRendererMixin(CapabilitiesRendererMixin, TablesetRendererMixin):

    def render_voresource(self, metadata):
        self.start('ri:Resource', {
            'created': metadata.get('created'),
            'updated': metadata.get('updated'),
            'status': metadata.get('voresource_status'),
            'xsi:type': metadata.get('vodataservice_type'),
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xmlns:ri': 'http://www.ivoa.net/xml/RegistryInterface/v1.0',
            'xmlns:vg': 'http://www.ivoa.net/xml/VORegistry/v1.0',
            'xmlns:vr': 'http://www.ivoa.net/xml/VOResource/v1.0',
            'xmlns:vs': 'http://www.ivoa.net/xml/VODataService/v1.2',
            'xsi:schemaLocation': 'http://www.ivoa.net/xml/RegistryInterface/v1.0 http://www.ivoa.net/xml/VORegistry/v1.0 http://www.ivoa.net/xml/VOResource/v1.0 http://www.ivoa.net/xml/VODataService/v1.2'
        })

        self.node('identifier', {}, metadata.get('identifier'))
        self.node('title', {}, metadata.get('title'))

        if metadata.get('short_name'):
            self.node('shortName', {}, metadata.get('short_name'))

        self.render_curation(metadata.get('curation', {}))
        self.render_content(metadata.get('content', {}))

        for capability in metadata.get('capabilities', []):
            self.render_capability(capability)

        tableset = metadata.get('tableset', [])
        if tableset:
            self.start('tableset')
            self.render_tableset(tableset)
            self.end('tableset')

        rights = metadata.get('rights')
        if rights:
            self.node('rights', {}, metadata.get('rights'))

        managed_authority = metadata.get('managed_authority')
        if managed_authority:
            self.node('managedAuthority', {}, managed_authority)

        managing_org = metadata.get('managing_org')
        if managing_org:
            self.node('managingOrg', {}, managing_org)

        self.end('ri:Resource')

    def render_curation(self, curation_metadata):
        self.start('curation')
        self.node('publisher', {}, curation_metadata.get('publisher'))
        self.node('date', {'role': 'updated'}, curation_metadata.get('date'))

        creator = curation_metadata.get('creator')
        if creator:
            self.start('creator')
            self.node('name', {}, creator.get('name'))
            self.node('logo', {}, creator.get('logo'))
            self.end('creator')

        contact = curation_metadata.get('contact')
        if contact:
            self.start('contact')
            self.node('name', {}, contact.get('name'))
            self.node('address', {}, contact.get('address'))
            self.node('email', {}, contact.get('email'))
            self.node('telephone', {}, contact.get('telephone'))
            self.end('contact')

        self.end('curation')

    def render_content(self, content_metadata):
        self.start('content')
        self.node('type', {}, content_metadata.get('type'))
        self.node('description', {}, content_metadata.get('description'))
        self.node('referenceURL', {}, content_metadata.get('referenceURL'))
        self.end('content')


class VoresourceRenderer(VoresourceRendererMixin, XMLRenderer):

    def render_document(self, data, accepted_media_type=None, renderer_context=None):
        self.render_voresource(data)