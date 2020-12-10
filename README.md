# NetWolf

NetWolf is a proof of concept for the distributed real time network monitoring and automation system capable of simultaneously interacting with thousands of network devices using vertical and horizontal scaling of resources. It consists of the manager program and number of agents. Agents can be spread out over multiple machines and bind separate processes to every available CPU core. Each of those processes maintains SSH connectivity to multiple network devices. To achieve high number of connections per core and the same time consume least amount of memory possible agent is internally based on Asyncio. Agent registers with manager and receives jobs that contain the hostname for the network device it's supposed to connect to and the set of commands that need execute on it. For the purpose of monitoring job can also contain filters that need to be applied to command output before its sent back to the manager.

For PoC purpose of PoC i have set it up to retrieve the CPU load from couple hundreds of Cisco switches and routers. Currently i was able to maintain around 350 SSH sessions using single core and pulling fresh data from each device every second. Obviously with this approach the number of monitored devices scales nicely with the number of CPU cores and number of machines being used by agents. NetWolf is in very early stage of development and at this point is nothing more than just a toy project. However it also has a good potential to be useful in production environment once it's mature enough.

#### Already implemented:

 - *simple hash based load balancing of the monitored devices across multiple agents - load is being spread out over multiple agents dynamically to account for the number of agents being registered with manager at given time*
 - *stateless job execution, SSH session to monitored device is maintained as long as agent periodically receives the 'job refresh' command, once agent stops being available all the jobs it was responsible for being transferred to other agents, in case manager stops being available agents 'age out' the jobs and wait till the connectivity to the manager can be restored*
 - *simple management protocol used to transfer jobs and results between manager and agents (the NetJson class)*
 - *ability for the agents to work on their jobs not being able to communicate with manager for limited period of time*
 - *as of now agents display the output data locally instead of sending it back to manager, this is more convenient for debugging purposes at this early stage of project*


#### To be implemented:

 - *load balancing based on consistent hash algorithm - this is not particularly useful for monitoring but may be more useful for automation purposes*
 - *stateful job execution, manager sends job to agent and keeps track of it till the report of completion is sent back or it times out - useful for automation purposes*
