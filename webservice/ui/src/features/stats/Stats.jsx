import React from "react";
import PropTypes from "prop-types";
import moment from "moment";
import DataBox from "components/data-box/DataBox";
import FontAwesome from "react-fontawesome";
import mq from "../../MqttClient";
import { MQTT, SETTINGS } from "../../constants/constants";
import "./Stats.css";
import Plot from 'react-plotly.js'

class Stats extends React.Component {
  constructor( props ) {
    super( props );

    this.handleMqtt = this.handleMqtt.bind( this );
    this.calculateClasses = this.calculateClasses.bind( this );
    this.calculateSpeed = this.calculateSpeed.bind( this );
    this.calculateSpeed1 = this.calculateSpeed1.bind( this );
    this.state = {
      currentClassCount: 0,
      currentFrameData: [],
      currentFrameLabels: [],
      currentSpeed: 0,
      currentSpeedData: [],
      currentSpeedLabels: [],
      currentSpeed1: 0,
      currentSpeedData1: [],
      currentSpeedLabels1: [],
    };
  }

  componentDidMount() {
    // register handler with mqtt client
    mq.addHandler( "class", this.handleMqtt );
  }

  componentWillUnmount() {
    mq.removeHandler( "class" );
  }

  handleMqtt( topic, payload ) {
    switch ( topic ) {
      case MQTT.TOPICS.CLASS:
        this.calculateClasses( payload );
        break;
      case MQTT.TOPICS.SPEEDOMETER:
        this.calculateSpeed( payload );
        break;
      case MQTT.TOPICS.SPEEDOMETER1:
        this.calculateSpeed1( payload );
        break;
      default:
        break;
    }
  }

  calculateClasses( input ) {
    let newLabel = this.state.currentFrameLabels;
    let newFrameData = this.state.currentFrameData;
    newLabel.push( input.class_names );
    if ( input.class_names.length != undefined ) {
      newFrameData.push( input.class_names.length );
    }
    if ( newFrameData.length > SETTINGS.MAX_POINTS ) {
      const sliceFrameData = newFrameData.slice( SETTINGS.SLICE_LENGTH );
      const sliceFrameLabels = newLabel.slice( SETTINGS.SLICE_LENGTH );
      newFrameData = sliceFrameData;
      newLabel = sliceFrameLabels;
    }
    this.setState( { currentClassCount: input.class_names.length,
      currentFrameLabels: newLabel,
      currentFrameData: newFrameData } );
  }

  calculateSpeed( input ) {
    let newLabel = this.state.currentSpeedLabels;
    let newFrameData = this.state.currentSpeedData;
    newLabel.push( input.speed );
    if ( input.speed != undefined ) {
      newFrameData.push( input.speed );
    }
    if ( newFrameData.length > SETTINGS.MAX_POINTS ) {
      const sliceFrameData = newFrameData.slice( SETTINGS.SLICE_LENGTH );
      const sliceFrameLabels = newLabel.slice( SETTINGS.SLICE_LENGTH );
      newFrameData = sliceFrameData;
      newLabel = sliceFrameLabels;
    }
    this.setState( { currentSpeed: input.speed,
      currentSpeedLabels: newLabel,
      currentSpeedData: newFrameData } );
  }
    
  calculateSpeed1( input ) {
    let newLabel = this.state.currentSpeedLabels1;
    let newFrameData = this.state.currentSpeedData1;
    newLabel.push( input.speed1 );
    if ( input.speed1 != undefined ) {
      newFrameData.push( input.speed1 );
    }
    if ( newFrameData.length > SETTINGS.MAX_POINTS ) {
      const sliceFrameData = newFrameData.slice( SETTINGS.SLICE_LENGTH );
      const sliceFrameLabels = newLabel.slice( SETTINGS.SLICE_LENGTH );
      newFrameData = sliceFrameData;
      newLabel = sliceFrameLabels;
    }
    this.setState( { currentSpeed1: input.speed1,
      currentSpeedLabels1: newLabel,
      currentSpeedData1: newFrameData } );
  }

  render() {
    return (
      <div className={ `stats ${ this.props.statsOn ? "active" : "" }` }>
        { /* Current class count */ }
        <DataBox title="Vehicles Count" data={ this.state.currentClassCount } />
        { /* Current speed */ }
        <DataBox title="People and Bikes Count" data={ this.state.currentSpeed } color="blue" />
          <div>
              <Plot
                  data={[
                      {
                          y:this.state.currentFrameData,
                          type:'line',
                          marker:{color:'#ff00ff'},
                          name:'Vehicles'
                      },
                      {
                          y:this.state.currentSpeedData,
                          type:'line',
                          marker:{color:'blue'},
                          name:'People and Bikes'
                      }
                  ]}
                  layout={{
                      width:'350',height:'400',
                      title:'Traffic Visualization',
                      showlegend: true,
                     plot_bgcolor: "lightgray",
                      legend: {"orientation": "h",
                              bfcolor:'lightgray',
                              bordercolor:'gray',
                              borderwidth:2},
                      margin: {
                        l: 35,
                        r: 60,
                        t:40
                       },
                      xaxis: {
                         autorange: 'reversed',
                        showgrid: false,
                        zeroline: false,
                        showline: false,
                        autotick: true,
                        ticks: '',
                        showticklabels: false
                      },
                      yaxis: {
                          title:'Count',
                          range: [0, 12],
                          autotick: false,
                            ticks: 'outside',
                            tick0: 0,
                            dtick: 1,
                            tickcolor: '#000'
                        }
                  }}
               />
                  
          </div>    
      </div>
    );
  }
}

Stats.propTypes = {
  statsOn: PropTypes.bool.isRequired,
};

Stats.defaultProps = {
};

export default Stats;
