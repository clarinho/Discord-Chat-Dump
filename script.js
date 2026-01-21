(async () => {
    // --- UI GENERATION ---
    const createUI = () => {
        return new Promise((resolve) => {
            const div = document.createElement("div");
            div.id = "archiver-container";
            div.innerHTML = `
                <div id="scraper-ui" style="position:fixed; top:15%; left:30%; width:420px; background:#313338; color:#dbdee1; padding:25px; border-radius:12px; border:1px solid #1e1f22; z-index:9999; font-family:sans-serif; box-shadow:0 12px 24px rgba(0,0,0,0.4);">
                    <h2 style="margin-bottom:10px; color:#fff; font-size:18px;">Discord Chat Archiver</h2>
                    <p style="font-size:12px; color:#b5bac1; margin-bottom:20px;">Fill in the details below to begin the extraction.</p>
                    
                    <label style="font-size:12px; font-weight:bold; color:#b5bac1;">TARGET USER ID</label><br>
                    <input id="u_id" placeholder="e.g. 012345678987654321" style="width:100%; background:#1e1f22; border:1px solid #232428; color:#fff; padding:10px; margin:8px 0 15px 0; border-radius:4px; box-sizing:border-box;"><br>
                    
                    <label style="font-size:12px; font-weight:bold; color:#b5bac1;">START DATE</label><br>
                    <input id="u_date" type="date" style="width:100%; background:#1e1f22; border:1px solid #232428; color:#fff; padding:10px; margin:8px 0 15px 0; border-radius:4px; box-sizing:border-box;"><br>
                    
                    <label style="font-size:12px; font-weight:bold; color:#b5bac1;">SERVER IDs (Comma Separated)</label><br>
                    <textarea id="u_guilds" placeholder="ID 1, ID 2, ID 3..." style="width:100%; height:70px; background:#1e1f22; border:1px solid #232428; color:#fff; padding:10px; margin:8px 0 15px 0; border-radius:4px; resize:none; box-sizing:border-box;"></textarea><br>
                    
                    <label style="font-size:12px; font-weight:bold; color:#b5bac1;">MAX MESSAGES PER SERVER</label><br>
                    <input id="u_max" type="number" value="10" style="width:100%; background:#1e1f22; border:1px solid #232428; color:#fff; padding:10px; margin:8px 0 20px 0; border-radius:4px; box-sizing:border-box;"><br>
                    
                    <button id="start-btn" style="width:100%; background:#5865f2; color:#fff; border:none; padding:12px; border-radius:4px; cursor:pointer; font-weight:bold; font-size:14px; transition: background 0.2s;">Start Extraction</button>
                    <button id="cancel-btn" style="width:100%; background:transparent; color:#fff; border:none; padding:8px; margin-top:5px; cursor:pointer; font-size:12px; text-decoration:underline;">Cancel</button>
                </div>
            `;
            document.body.appendChild(div);

            document.getElementById("cancel-btn").onclick = () => { div.remove(); };
            
            document.getElementById("start-btn").onclick = () => {
                const uId = document.getElementById("u_id").value.trim();
                const uDate = document.getElementById("u_date").value;
                const uGuilds = document.getElementById("u_guilds").value.trim();
                
                if(!uId || !uDate || !uGuilds) {
                    alert("Please fill in the User ID, Date, and at least one Server ID.");
                    return;
                }

                const data = {
                    userId: uId,
                    startDate: uDate,
                    guildIds: uGuilds.split(",").map(id => id.trim()).filter(id => id.length > 0),
                    maxMsgs: parseInt(document.getElementById("u_max").value) || 10
                };
                div.remove();
                resolve(data);
            };
        });
    };

    const config = await createUI();
    const TARGET_USER_ID = config.userId;
    const START_DATE = config.startDate;
    const DEBUG_GUILD_IDS = config.guildIds;
    const MAX_MSGS_PER_SERVER = config.maxMsgs;

    // --- CORE LOGIC ---
    const getSnowflake = (dateString) => {
        const date = new Date(dateString);
        return (BigInt(date.getTime()) - 1420070400000n) << 22n;
    };
    const minId = getSnowflake(START_DATE).toString();

    const wpRequire = webpackChunkdiscord_app.push([[Symbol()], {}, r => r]);
    const api = Object.values(wpRequire.c).find(x => x?.exports?.tn?.get).exports.tn;
    const findStore = (filter) => Object.values(wpRequire.c).find(x => x?.exports?.Z && filter(x.exports.Z))?.exports?.Z;
    
    const GuildStore = findStore(s => s.getGuilds && !s.getChannel);
    const GuildChannelsStore = findStore(s => s.getChannels && s.getSelectableChannelIds);

    const masterResults = [];
    console.log(`%c[INITIALIZED] Targeting User: ${TARGET_USER_ID}`, "color: #5865F2; font-weight: bold;");

    for (const guildId of DEBUG_GUILD_IDS) {
        const guild = GuildStore.getGuild(guildId);
        if (!guild) {
            console.warn(`Server ID ${guildId} not found in your account.`);
            continue;
        }

        console.log(`%cScanning: ${guild.name}`, "color: #B9BBBE;");

        // Stealth behavior: Simulate navigation
        const channelsInGuild = GuildChannelsStore.getChannels(guild.id).SELECTABLE || [];
        const textChannel = channelsInGuild.find(c => c.type === 0);
        if (textChannel) {
            await api.get({ url: `/channels/${textChannel.id}/messages?limit=2` });
            await new Promise(r => setTimeout(r, 1500 + Math.random() * 1000));
        }

        let offset = 0;
        let hasMore = true;
        let serverMatchCount = 0;

        while (hasMore) {
            try {
                const response = await api.get({ 
                    url: `/guilds/${guild.id}/messages/search?author_id=${TARGET_USER_ID}&min_id=${minId}&offset=${offset}` 
                });
                const data = response.body;
                
                const channelMap = {};
                if (data.threads) data.threads.forEach(t => channelMap[t.id] = t);
                if (data.channels) data.channels.forEach(c => channelMap[c.id] = c);

                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(group => {
                        const msg = group.find(m => m.author.id === TARGET_USER_ID);
                        if (msg && serverMatchCount < MAX_MSGS_PER_SERVER) {
                            const chanInfo = channelMap[msg.channel_id];
                            const attachments = msg.attachments ? msg.attachments.map(a => ({
                                filename: a.filename,
                                url: a.url
                            })) : [];

                            masterResults.push({
                                server: guild.name,
                                category: (chanInfo && chanInfo.parent_id) ? (channelMap[chanInfo.parent_id]?.name || "Unknown Category") : "No Category",
                                channel: chanInfo ? chanInfo.name : "unknown-channel",
                                date: msg.timestamp,
                                content: msg.content,
                                attachments: attachments
                            });
                            serverMatchCount++;
                        }
                    });

                    offset += 25;
                    if (offset >= data.total_results || serverMatchCount >= MAX_MSGS_PER_SERVER) hasMore = false;
                    await new Promise(r => setTimeout(r, 2000 + Math.random() * 1500)); 
                } else {
                    hasMore = false;
                }
            } catch (e) {
                hasMore = false;
                await new Promise(r => setTimeout(r, 5000));
            }
        }
        console.log(`%c[DONE] Found ${serverMatchCount} matches in "${guild.name}".`, "color: #43B581;");
        await new Promise(r => setTimeout(r, 7000 + Math.random() * 3000)); 
    }

    const blob = new Blob([JSON.stringify(masterResults, null, 4)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `chats.json`;
    link.click();
    console.log("%c[COMPLETE] chats.json has been saved.", "color: #5865F2; font-weight: bold;");
})();