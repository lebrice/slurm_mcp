from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Dict, Any


class Comment(BaseModel):
    administrator: str
    job: str
    system: str


class ArrayLimitsRunningTasks(BaseModel):
    tasks: int


class ArrayLimitsMax(BaseModel):
    running: ArrayLimitsRunningTasks


class ArrayLimits(BaseModel):
    max: ArrayLimitsMax


class ArrayTaskId(BaseModel):
    set: bool
    infinite: bool
    number: int


class Array(BaseModel):
    job_id: int
    limits: ArrayLimits
    task_id: ArrayTaskId
    task: str


class Association(BaseModel):
    account: str
    cluster: str
    partition: str
    user: str
    id: int


class DerivedExitCodeReturnCode(BaseModel):
    set: bool
    infinite: bool
    number: int


class DerivedExitCodeSignalId(BaseModel):
    set: bool
    infinite: bool
    number: int


class DerivedExitCodeSignal(BaseModel):
    id: DerivedExitCodeSignalId
    name: str


class DerivedExitCode(BaseModel):
    status: List[str]
    return_code: DerivedExitCodeReturnCode
    signal: DerivedExitCodeSignal


class TimePlanned(BaseModel):
    set: bool
    infinite: bool
    number: int


class TimeLimit(BaseModel):
    set: bool
    infinite: bool
    number: int


class TimeTotal(BaseModel):
    seconds: int
    microseconds: int


class TimeUser(BaseModel):
    seconds: int
    microseconds: int


class TimeSystem(BaseModel):
    seconds: int
    microseconds: int


class Time(BaseModel):
    elapsed: int
    eligible: int
    end: int
    planned: TimePlanned
    start: int
    submission: int
    suspended: int
    system: TimeSystem
    limit: TimeLimit
    total: TimeTotal
    user: TimeUser


class ExitCodeReturnCode(BaseModel):
    set: bool
    infinite: bool
    number: int


class ExitCodeSignalId(BaseModel):
    set: bool
    infinite: bool
    number: int


class ExitCodeSignal(BaseModel):
    id: ExitCodeSignalId
    name: str


class ExitCode(BaseModel):
    status: List[str]
    return_code: ExitCodeReturnCode
    signal: ExitCodeSignal


class State(BaseModel):
    current: List[str]
    reason: str


# Job Step Models
class StepTimeEnd(BaseModel):
    set: bool
    infinite: bool
    number: int


class StepTimeStart(BaseModel):
    set: bool
    infinite: bool
    number: int


class StepTimeLimit(BaseModel):
    set: bool
    infinite: bool
    number: int


class StepTimeTotal(BaseModel):
    seconds: int
    microseconds: int


class StepTimeUser(BaseModel):
    seconds: int
    microseconds: int


class StepTimeSystem(BaseModel):
    seconds: int
    microseconds: int


class StepTime(BaseModel):
    elapsed: int
    end: StepTimeEnd
    start: StepTimeStart
    suspended: int
    system: StepTimeSystem
    limit: StepTimeLimit
    total: StepTimeTotal
    user: StepTimeUser


class StepExitCodeReturnCode(BaseModel):
    set: bool
    infinite: bool
    number: int


class StepExitCodeSignalId(BaseModel):
    set: bool
    infinite: bool
    number: int


class StepExitCodeSignal(BaseModel):
    id: StepExitCodeSignalId
    name: str


class StepExitCode(BaseModel):
    status: List[str]
    return_code: StepExitCodeReturnCode
    signal: StepExitCodeSignal


class StepNodes(BaseModel):
    count: int
    range: str
    list: List[str]


class StepTasks(BaseModel):
    count: int


class StepCPURequestedFrequencyMin(BaseModel):
    set: bool
    infinite: bool
    number: int


class StepCPURequestedFrequencyMax(BaseModel):
    set: bool
    infinite: bool
    number: int


class StepCPURequestedFrequency(BaseModel):
    min: StepCPURequestedFrequencyMin
    max: StepCPURequestedFrequencyMax


class StepCPU(BaseModel):
    requested_frequency: StepCPURequestedFrequency
    governor: str


class StepStatisticsCPU(BaseModel):
    actual_frequency: int


class StepStatisticsEnergyConsumed(BaseModel):
    set: bool
    infinite: bool
    number: int


class StepStatisticsEnergy(BaseModel):
    consumed: StepStatisticsEnergyConsumed


class StepStatistics(BaseModel):
    CPU: StepStatisticsCPU
    energy: StepStatisticsEnergy


class StepInfo(BaseModel):
    id: str
    name: str
    stderr: str
    stdin: str
    stdout: str
    stderr_expanded: str
    stdin_expanded: str
    stdout_expanded: str


class StepTask(BaseModel):
    distribution: str


class TresResource(BaseModel):
    type: str
    name: str
    id: int
    count: int
    task: int = 0
    node: str = ""


class TresResourceSimple(BaseModel):
    type: str
    name: str
    id: int
    count: int


class TresRequested(BaseModel):
    max: List[TresResource]
    min: List[TresResource]
    average: List[TresResourceSimple]
    total: List[TresResourceSimple]


class TresConsumed(BaseModel):
    max: List[TresResource]
    min: List[TresResource]
    average: List[TresResourceSimple]
    total: List[TresResourceSimple]


class Tres(BaseModel):
    requested: TresRequested
    consumed: TresConsumed
    allocated: List[TresResourceSimple]

    def num_allocated_gpus(self) -> int:
        for res in self.allocated:
            if res.type == "gres" and res.name == "gpu":
                return res.count
        return 0


class JobStep(BaseModel):
    time: StepTime
    exit_code: StepExitCode
    nodes: StepNodes
    tasks: StepTasks
    pid: str
    CPU: StepCPU
    kill_request_user: str
    state: List[str]
    statistics: StepStatistics
    step: StepInfo
    task: StepTask
    tres: Tres


class SlurmJob(BaseModel):
    account: str
    comment: Comment
    allocation_nodes: int
    array: Array
    association: Association
    block: str
    cluster: str
    constraints: str
    container: str
    derived_exit_code: DerivedExitCode
    time: Time
    exit_code: ExitCode
    extra: str
    failed_node: str
    flags: List[str]
    group: str
    job_id: int
    name: str
    licenses: str
    nodes: str
    partition: str
    hold: bool
    priority: Dict[str, Any]
    qos: str
    qosreq: str
    required: Dict[str, Any]
    kill_request_user: str
    restart_cnt: int
    reservation: Dict[str, Any]
    script: str
    segment_size: int
    stdin_expanded: str
    stdout_expanded: str
    stderr_expanded: str
    stdout: str
    stderr: str
    stdin: str
    state: State
    steps: List[JobStep]

    # Add other fields as needed
    @property
    def elapsed_time(self) -> float:
        return float(self.time.elapsed)

    @property
    def elapsed_td(self) -> timedelta:
        return timedelta(seconds=self.time.elapsed)

    @property
    def start_time(self) -> datetime:
        return datetime.fromtimestamp(self.time.start)

    @property
    def end_time(self) -> datetime:
        return datetime.fromtimestamp(self.time.end)


class SacctOutput(BaseModel):
    jobs: List[SlurmJob]
