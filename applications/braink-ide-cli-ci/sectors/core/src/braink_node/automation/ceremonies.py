
def run(context):
    deployment = context.manager.deploy(context.catalogue())
    return {'state': 'READBACK', 'catalogue_sha256': deployment['catalogue_sha256'], 'instances': len(deployment['instances']),
            'sectors': deployment['sectors'], 'manifest': 'instances/deployment.json'}
