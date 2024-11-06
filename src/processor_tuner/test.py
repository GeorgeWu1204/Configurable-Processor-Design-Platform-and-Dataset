import re



# # Start with the simplest regex to match class keyword and name
# # simple_pattern = re.compile(r'class\s+WithCustomisedCore\(\s*n:\s*Int,\s*crossing:\s*RocketCrossingParams\s*=\s*RocketCrossingParams\(\s*\),\s*\)\s*extends\s*Config\(\(site,\s*here,\s*up\)\s*=>\s*{' 
# #                             r'(.*?)'  # Captures all configurations within the Config block
# #                             r'}\)', re.DOTALL)
# simple_pattern = re.compile(
#     r'class\s+WithCustomisedCore\(\s*n:\s*Int,\s*crossing:\s*RocketCrossingParams\s*=\s*RocketCrossingParams\(\s*\),\s*\)\s*extends\s'
#     r'(.*?)}\)', re.DOTALL)

# simple_match = simple_pattern.search(scala_code)
# if simple_match:
#     print("Match found for class name.")
#     print(simple_match.group(2))
# else:
#     print("No match found for class name.")


def modify_scala_code(params_name, input_vals, scala_code):
    print(params_name)
    print(input_vals)

    # Regular expression to find the WithCustomisedCore class definition
    class_pattern = re.compile(
        r'class\s+WithCustomisedCore\(\s*n:\s*Int,\s*crossing:\s*RocketCrossingParams\s*=\s*RocketCrossingParams\(\s*\),\s*\)\s*extends\s*Config\(\(site,\s*here,\s*up\)\s*=>\s*{\s*(.*?)\s*}\)',
        re.DOTALL)

    match = class_pattern.search(scala_code)

    if match:
        print("WithCustomisedCore class definition found.")
        config_body = match.group(1)  # Corrected to match the single capture group
        for var_name, var_val in zip(params_name, input_vals):
            print(var_name, var_val)
            class_name, sub_name = var_name.split('_')
            if class_name == 'icache':
                pattern = re.compile(rf'icache\s*=\s*Some\(ICacheParams\((.*?)\)\)', re.DOTALL)
                cache_match = pattern.search(config_body)
            elif class_name == 'dcache':
                pattern = re.compile(rf'dcache\s*=\s*Some\(DCacheParams\((.*?)\)\)', re.DOTALL)
                cache_match = pattern.search(config_body)
            if cache_match:
                params = cache_match.group(1)
                sub_pattern = re.compile(rf'{sub_name}\s*=\s*\d+')
                if sub_pattern.search(params):
                    new_params = sub_pattern.sub(f'{sub_name} = {var_val}', params)
                    new_cache_body = cache_match.group(0).replace(params, new_params)
                    config_body = config_body.replace(cache_match.group(0), new_cache_body)
                else:
                    print(f"{sub_name} not found in {class_name} parameters.")
            else:
                print(f"{class_name} class not found in the body.")
        
        # Rewrite the modified block back into the scala_code
        scala_code = class_pattern.sub(f'class WithCustomisedCore(n: Int, crossing: RocketCrossingParams = RocketCrossingParams()) extends Config((site, here, up) => {{{config_body}}})', scala_code)

        print(scala_code)
    else:
        print("WithCustomisedCore class definition not found.")

scala_code = """class WithCustomisedCore( 
  n: Int,
  crossing: RocketCrossingParams = RocketCrossingParams(),
) extends Config((site, here, up) => {
  case TilesLocated(InSubsystem) => {
    val prev = up(TilesLocated(InSubsystem), site)
    val idOffset = up(NumTiles)
    val med = RocketTileParams(
      core = RocketCoreParams(fpu = None),
      btb = None,
      dcache = Some(DCacheParams(
        rowBits = site(SystemBusKey).beatBits,
        nSets = 64,
        nWays = 1,
        nTLBSets = 1,
        nTLBWays = 4,
        nMSHRs = 0,
        blockBytes = site(CacheBlockBytes))),
      icache = Some(ICacheParams(
        rowBits = site(SystemBusKey).beatBits,
        nSets = 64,
        nWays = 1,
        nTLBSets = 1,
        nTLBWays = 4,
        blockBytes = site(CacheBlockBytes)))
    )
    List.tabulate(n)(i => RocketTileAttachParams(
      med.copy(tileId = i + idOffset),
      crossing
    )) ++ prev
  }
  case NumTiles => up(NumTiles) + n
})"""
modify_scala_code( ['icache_nWays', 'dcache_nSets', 'dcache_nWays', 'icache_nTLBSets', 'icache_nTLBWays'], [28, 38, 18, 42, 14], scala_code)
