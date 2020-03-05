from .action import Action
from .movebkpperiod import MoveBkpPeriod
from .tar_archiver import TarArchiver
from .check_last_backup import CheckLastBackup
from .pgdump import PgDump
from .cleaner import Cleaner
from .dataspace_checker import DataSpaceChecker
from .in_progress_ticket import (CheckInProgressTicket, SetInProgressTicket,
                                 UnsetInProgressTicket)
from .umount import Umount
from .mount import Mount
from .rsync import Rsync


action_types = (
    ('action', Action),
    ('tar', TarArchiver),
    ('cleaner', Cleaner),
    ('rsync', Rsync),
    ('pgdump', PgDump),
    ('dschecker', DataSpaceChecker),
    ('check_backup', CheckLastBackup),
    ('mount', Mount),
    ('umount', Umount),
    ('move_bkp_period', MoveBkpPeriod),
    ('set_in_progress_ticket', SetInProgressTicket),
    ('unset_in_progress_ticket', UnsetInProgressTicket),
    ('check_in_progress_ticket', CheckInProgressTicket),
)
