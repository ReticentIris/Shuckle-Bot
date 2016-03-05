from .db import session_factory
from .models.status import ModuleStatus

def is_enabled(module, channel):
    with session_factory() as sess:
        try:
            query = sess.query(ModuleStatus.status).filter(
                ModuleStatus.channel==channel,
                ModuleStatus.module==module
            ).one()

            return query.status != 0
        except:
            return True

def enable(module, channel):
    with session_factory() as sess:
        query = sess.query(ModuleStatus).filter(
            ModuleStatus.channel==channel,
            ModuleStatus.module==module
        )

        if query.exists():
            status = query.one()
        else:
            status = ModuleStatus(channel=channel, module=module)

        status.status = True
        status.save()

def disable(module, channel):
    with session_factory() as sess:
        query = sess.query(ModuleStatus).filter(
            ModuleStatus.channel==channel,
            ModuleStatus.module==module
        )

        if query.exists():
            status = query.one()
        else:
            status = ModuleStatus(channel=channel, module=module)

        status.status = False
        status.save()
