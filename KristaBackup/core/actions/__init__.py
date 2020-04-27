from .action import Action
from .movebkpperiod import MoveBkpPeriod
from .script import Command, Script
from .archiver import Archiver, ArchiverTar, ArchiverZip
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
    ('command', Command),
    ('script', Script),
    ('arhiver', Archiver),
    ('tar', ArchiverTar),
    ('zip', ArchiverZip),
    ('pgdump', PgDump),
    ('cleaner', Cleaner),
    ('rsync', Rsync),
    ('dschecker', DataSpaceChecker),
    ('check_backup', CheckLastBackup),
    ('mount', Mount),
    ('umount', Umount),
    ('move_bkp_period', MoveBkpPeriod),
    ('set_in_progress_ticket', SetInProgressTicket),
    ('unset_in_progress_ticket', UnsetInProgressTicket),
    ('check_in_progress_ticket', CheckInProgressTicket),
)
