# NetWolf

NetWolf is a proof of concept for the distributed real time network monitoring / automation system capable of simultaneously interacting with thousands of network devices. It maintains SSH connectivity to the network devices and periodically extracts or deploys desired data using CLI commands. For scalability purpose it consist of the manager program and number of agents. Agent binds separate process to every available single CPU core and each of those processes maintains SSH connectivity to multiple network devices. Agents can be deployed on multiple machines to scale the number of monitored network devices. To achieve high number of connections and the same time consume least amount of memory possible agent is internally based on Asyncio. Each agent also establishes its own TCP session with the manager program. Once agent registers with manager it receives jobs that consist of the hostname of monitored device and the set of commands that need to be executed on the device. It also contains description of the data that needs to be extracted from the device's command outputs and send back to the manager. For the PoC purpose it is used to retrieve the CPU load from couple hundreds of Cisco switches and routers i have available in my environment. Currently i was able to maintain around 350 SSH sessions using single core and pulling fresh data from each device every second. Obviously with this approach the number of monitored devices scales nicely with the number of CPU cores being used.

NetWolf is in very early stage of development and at this point is nothing more than just a toy project. However it also has a good potential to be useful in production environment once it's mature enough.

#### Already implemented:

 - *simple hash based load balancing of the monitored devices across multiple agents*
 - *stateless job execution, SSH session to monitored device is maintained as long as agent periodically receives the 'job refresh' command, once agent stops being available all the jobs it was responsible for being transferred to other agents, in case manager stops being available agents 'age out' the jobs and wait till the connectivity to the manager can be restored*
 - *agents display the output data locally instead of sending it back to manager, this is more convenient for debugging purposes at this early stage of project*


#### To be implemented:

 - *load balancing based on consistent hash algorithm*
 - *stateful job execution, manager sends job to agent and keeps track of it till the report of completion is sent back or it times out*
 - *ability for the agents to work on their jobs not being able to communicate with  manager for limited period of time*
